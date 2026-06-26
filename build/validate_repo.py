#!/usr/bin/env python3
"""
TX Bionic Repository Validator
Validates all packages in the repository for Android Bionic compatibility.
"""

import os
import sys
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_DIR = Path(__file__).parent.parent / "repo" / "stable"
PKG_DIR = REPO_DIR / "packages"

def log(msg, level="INFO"):
    print(f"[{level}] {msg}")

def sha256_file(filepath):
    import hashlib
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def validate_binary(filepath):
    """Validate a single binary file for Android Bionic compatibility."""
    errors = []
    warnings = []
    info = {}
    
    # Check with 'file' command
    try:
        result = subprocess.run(
            ["file", str(filepath)],
            capture_output=True, text=True, timeout=15
        )
        file_output = result.stdout
    except Exception as e:
        return {"valid": False, "errors": [f"file command failed: {e}"]}
    
    info["file_output"] = file_output.strip()
    
    # Must be ARM64
    if "ARM aarch64" not in file_output and "aarch64" not in file_output:
        errors.append("Not AArch64 architecture")
    else:
        info["arch"] = "aarch64"
    
    # Must be PIE, shared object, or relocatable (compiler artifacts)
    is_pie = "pie executable" in file_output.lower() or "PIE" in file_output
    is_so = "shared object" in file_output.lower()
    is_rel = "relocatable" in file_output.lower()
    if not (is_pie or is_so or is_rel):
        # Check with readelf
        try:
            re = subprocess.run(
                ["readelf", "-h", str(filepath)],
                capture_output=True, text=True, timeout=10
            )
            if "Type:                               DYN" not in re.stdout and "Type:                               REL" not in re.stdout:
                errors.append("Not a PIE executable, shared library, or relocatable object")
            else:
                is_pie = True
        except:
            errors.append("Could not verify PIE status")
    
    info["pie"] = is_pie or is_so or is_rel
    
    # Must NOT use musl
    if "ld-musl" in file_output:
        errors.append("Uses musl libc interpreter")
    if "musl" in file_output:
        warnings.append("References musl in file output")
    
    # Must NOT use glibc
    if "ld-linux" in file_output:
        errors.append("Uses glibc interpreter")
    
    # Check readelf -l for interpreter
    try:
        result = subprocess.run(
            ["readelf", "-l", str(filepath)],
            capture_output=True, text=True, timeout=10
        )
        readelf_l = result.stdout
        
        if "Requesting program interpreter" in readelf_l:
            for line in readelf_l.split("\n"):
                if "interpreter" in line.lower():
                    interp = line.strip()
                    info["interpreter"] = interp
                    
                    if "ld-musl" in interp:
                        errors.append(f"Musl interpreter detected: {interp}")
                    elif "ld-linux" in interp:
                        errors.append(f"Glibc interpreter detected: {interp}")
                    elif "linker" in interp:
                        info["bionic"] = True
                    break
        else:
            info["interpreter"] = "(none - static/library/relocatable)"
            info["bionic"] = True
    except Exception as e:
        warnings.append(f"readelf -l failed: {e}")
    
    # Check readelf -d for library dependencies
    try:
        result = subprocess.run(
            ["readelf", "-d", str(filepath)],
            capture_output=True, text=True, timeout=10
        )
        readelf_d = result.stdout
        
        needed = []
        for line in readelf_d.split("\n"):
            if "NEEDED" in line:
                lib = line.split("[", 1)[1].split("]", 1)[0] if "[" in line else ""
                needed.append(lib)
        
        info["needed"] = needed
        
        for lib in needed:
            if "musl" in lib:
                errors.append(f"Depends on musl library: {lib}")
            if "glibc" in lib.lower() or "libc.so.6" == lib:
                errors.append(f"Depends on glibc library: {lib}")
    except Exception as e:
        warnings.append(f"readelf -d failed: {e}")
    
    # Check with objdump -p
    try:
        result = subprocess.run(
            ["objdump", "-p", str(filepath)],
            capture_output=True, text=True, timeout=10
        )
        objdump_out = result.stdout
        
        if "NEEDED" in objdump_out:
            needed2 = []
            for line in objdump_out.split("\n"):
                if "NEEDED" in line:
                    lib = line.strip().split()[-1] if line.strip() else ""
                    if lib:
                        needed2.append(lib)
            info["objdump_needed"] = needed2
    except Exception as e:
        warnings.append(f"objdump -p failed: {e}")
    
    is_valid = len(errors) == 0 and info.get("bionic", False) and info.get("arch") == "aarch64"
    
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "info": info,
    }

def validate_txpkg(txpkg_path):
    """Validate a single .txpkg archive."""
    txpkg_path = Path(txpkg_path)
    name = txpkg_path.stem
    pkg_name = name.split("-")[0] if "-" in name else name
    
    # Packages that skip binary validation (compiler artifacts, headers-only)
    skip_binary_packages = {"ndk-sysroot", "libstdc++"}
    
    result = {
        "name": name,
        "txpkg": str(txpkg_path.name),
        "valid": False,
        "errors": [],
        "warnings": [],
        "binaries_checked": 0,
        "binaries_valid": 0,
        "binaries_invalid": 0,
    }
    
    # Check file exists and is readable
    if not txpkg_path.exists():
        result["errors"].append("File does not exist")
        return result
    
    # Check it's a valid tar.xz
    try:
        with tarfile.open(txpkg_path, "r:xz") as tar:
            members = tar.getnames()
    except Exception as e:
        result["errors"].append(f"Invalid tar.xz archive: {e}")
        return result
    
    # Check required members
    required = {"CONTROL", "manifest.json", "checksums"}
    missing = required - set(members)
    if missing:
        result["errors"].append(f"Missing required members: {missing}")
    
    has_files = any(m.startswith("files/") for m in members)
    if not has_files:
        result["errors"].append("No files/ directory in package")
    
    # Extract and validate binaries (unless skip_binary_check is set)
    skip_binaries = pkg_name in skip_binary_packages
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        with tarfile.open(txpkg_path, "r:xz") as tar:
            tar.extractall(tmpdir)
        
        files_dir = tmpdir / "files"
        if not files_dir.exists():
            result["errors"].append("files/ directory not extracted")
            return result
        
        if not skip_binaries:
            # Validate binaries
            for filepath in files_dir.rglob("*"):
                # Skip symlinks - their targets will be checked directly
                if filepath.is_symlink():
                    continue
                
                if not filepath.is_file():
                    continue
                
                # Check if ELF
                try:
                    with open(filepath, "rb") as f:
                        magic = f.read(4)
                        if magic != b"\x7fELF":
                            continue
                except Exception:
                    continue
                
                result["binaries_checked"] += 1
                rel_path = str(filepath.relative_to(files_dir))
                
                vresult = validate_binary(filepath)
                
                if vresult["valid"]:
                    result["binaries_valid"] += 1
                else:
                    result["binaries_invalid"] += 1
                    result["errors"].extend(
                        f"[{rel_path}] {e}" for e in vresult["errors"]
                    )
                result["warnings"].extend(
                    f"[{rel_path}] {w}" for w in vresult["warnings"]
                )
        else:
            # Binary check skipped for this package type
            result["binaries_checked"] = 0
            result["binaries_valid"] = 0
            result["warnings"].append("Binary validation skipped (compiler artifacts package)")
    
    # Overall validity
    result["valid"] = len(result["errors"]) == 0
    return result

def validate_repository():
    """Validate all packages in the repository."""
    log("=" * 60)
    log("TX Bionic Repository Validator")
    log("=" * 60)
    
    # Find all .txpkg files
    txpkg_files = sorted(PKG_DIR.glob("*.txpkg"))
    log(f"Found {len(txpkg_files)} .txpkg files")
    
    if not txpkg_files:
        log("No packages found to validate!")
        return False
    
    # Validate Packages.json
    packages_json_path = REPO_DIR / "Packages.json"
    if packages_json_path.exists():
        with open(packages_json_path) as f:
            try:
                pkg_data = json.load(f)
                log(f"Packages.json: {pkg_data.get('package_count', '?')} packages listed")
                if pkg_data.get("target") != "android-bionic":
                    log("WARNING: Packages.json does not indicate android-bionic target", "WARN")
            except json.JSONDecodeError as e:
                log(f"Invalid Packages.json: {e}", "ERROR")
    else:
        log("Packages.json not found!", "ERROR")
    
    # Validate index.json
    index_json_path = REPO_DIR / "index.json"
    if index_json_path.exists():
        with open(index_json_path) as f:
            try:
                idx_data = json.load(f)
                log(f"index.json: {idx_data.get('packages_count', '?')} packages")
            except json.JSONDecodeError as e:
                log(f"Invalid index.json: {e}", "ERROR")
    else:
        log("index.json not found!", "ERROR")
    
    # Validate SHA256SUMS
    sha256sums_path = REPO_DIR / "SHA256SUMS"
    if sha256sums_path.exists():
        log("SHA256SUMS file present")
    else:
        log("SHA256SUMS not found!", "ERROR")
    
    # Validate each package
    log("\nValidating packages...")
    log("-" * 60)
    
    results = []
    for txpkg_path in txpkg_files:
        result = validate_txpkg(txpkg_path)
        results.append(result)
        
        status = "PASS" if result["valid"] else "FAIL"
        binaries = f"({result['binaries_valid']}/{result['binaries_checked']} binaries OK)"
        
        if result["valid"]:
            log(f"  [{status}] {result['txpkg']:50s} {binaries}")
        else:
            log(f"  [{status}] {result['txpkg']:50s} {binaries}")
            for err in result["errors"]:
                log(f"         ERROR: {err}", "ERROR")
    
    # Summary
    log("\n" + "=" * 60)
    log("VALIDATION SUMMARY")
    log("=" * 60)
    
    total = len(results)
    valid = sum(1 for r in results if r["valid"])
    invalid = total - valid
    
    total_binaries = sum(r["binaries_checked"] for r in results)
    valid_binaries = sum(r["binaries_valid"] for r in results)
    
    log(f"Packages: {valid}/{total} valid")
    log(f"Binaries: {valid_binaries}/{total_binaries} valid")
    
    if invalid > 0:
        log(f"\n{invalid} packages FAILED validation:")
        for r in results:
            if not r["valid"]:
                log(f"  - {r['txpkg']}")
    
    # Check for forbidden references
    log("\n--- Forbidden Reference Check ---")
    musl_refs = 0
    glibc_refs = 0
    
    for r in results:
        for err in r["errors"]:
            if "musl" in err.lower():
                musl_refs += 1
            if "glibc" in err.lower():
                glibc_refs += 1
    
    log(f"Musl references found: {musl_refs}")
    log(f"Glibc references found: {glibc_refs}")
    
    if musl_refs == 0 and glibc_refs == 0:
        log("No forbidden libc references found!")
    
    return invalid == 0

if __name__ == "__main__":
    success = validate_repository()
    sys.exit(0 if success else 1)
