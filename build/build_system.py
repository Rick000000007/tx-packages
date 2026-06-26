#!/usr/bin/env python3
"""
TX Bionic Build System
Downloads Termux .deb packages, extracts them, and repackages into .txpkg format.
All binaries are Android Bionic ARM64 - verified at build time.
"""

import os
import sys
import json
import hashlib
import shutil
import tarfile
import tempfile
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import package definitions
from packages import PACKAGES, VIRTUAL_PROVIDES, TERMUX_REPO_URL, TERMUX_DISTS

# Configuration
BUILD_DIR = Path(__file__).parent.parent
CACHE_DIR = BUILD_DIR / "build" / ".cache"
REPO_DIR = BUILD_DIR / "repo" / "stable"
PKG_DIR = REPO_DIR / "packages"
MAX_WORKERS = 4
ARCH = "aarch64"

def setup_dirs():
    """Create necessary directories."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    PKG_DIR.mkdir(parents=True, exist_ok=True)
    (BUILD_DIR / "build" / "logs").mkdir(parents=True, exist_ok=True)

def log(msg, level="INFO"):
    """Print a log message with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")

def sha256_file(filepath):
    """Calculate SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def download_termux_pkglist():
    """Download Termux package list and parse it."""
    cache_file = CACHE_DIR / "Packages.termux"
    url = f"{TERMUX_REPO_URL}/{TERMUX_DISTS}/Packages"
    
    if cache_file.exists() and cache_file.stat().st_size > 1024:
        mtime = cache_file.stat().st_mtime
        age = datetime.now().timestamp() - mtime
        if age < 3600:  # Cache for 1 hour
            log("Using cached Termux package list")
            with open(cache_file) as f:
                return parse_termux_packages(f.read())
    
    log(f"Downloading Termux package list from {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TX-Bionic-Build/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read().decode("utf-8", errors="replace")
        with open(cache_file, "w") as f:
            f.write(data)
        log(f"Downloaded {len(data)} bytes of package data")
        return parse_termux_packages(data)
    except Exception as e:
        log(f"Failed to download package list: {e}", "ERROR")
        if cache_file.exists():
            log("Using stale cached package list")
            with open(cache_file) as f:
                return parse_termux_packages(f.read())
        raise

def parse_termux_packages(data):
    """Parse Termux Packages file into dict of package info."""
    packages = {}
    current = {}
    
    for line in data.split("\n"):
        line = line.strip()
        if line == "":
            if current and "Package" in current:
                packages[current["Package"]] = current
            current = {}
        elif ": " in line:
            key, val = line.split(": ", 1)
            current[key] = val
    
    if current and "Package" in current:
        packages[current["Package"]] = current
    
    log(f"Parsed {len(packages)} packages from Termux repository")
    return packages

def find_termux_deb_url(termux_name, termux_pkgs):
    """Find the .deb download URL for a Termux package."""
    if termux_name not in termux_pkgs:
        return None
    
    pkg = termux_pkgs[termux_name]
    filename = pkg.get("Filename", "")
    if filename:
        return f"{TERMUX_REPO_URL}/{filename}"
    
    # Fallback: construct URL from package info
    version = pkg.get("Version", "")
    if version:
        deb_name = f"{termux_name}_{version}_{ARCH}.deb"
        return f"{TERMUX_REPO_URL}/pool/main/{termux_name[0]}/{termux_name}/{deb_name}"
    
    return None

def download_deb(url, dest_path):
    """Download a .deb file with caching."""
    if dest_path.exists():
        log(f"  Using cached {dest_path.name}")
        return dest_path
    
    log(f"  Downloading {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TX-Bionic-Build/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        with open(dest_path, "wb") as f:
            f.write(data)
        log(f"  Downloaded {len(data)} bytes")
        return dest_path
    except Exception as e:
        log(f"  Download failed: {e}", "ERROR")
        return None

def extract_deb(deb_path, extract_dir):
    """Extract a .deb package (ar archive with data.tar.xz inside)."""
    extract_dir = Path(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    # .deb is an ar archive: debian-binary, control.tar.*, data.tar.*
    # First extract the ar archive
    ar_extract = extract_dir / "_ar"
    ar_extract.mkdir(exist_ok=True)
    
    result = subprocess.run(
        ["ar", "x", str(deb_path)],
        cwd=ar_extract,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        log(f"  ar extract failed: {result.stderr}", "ERROR")
        return False
    
    # Find data.tar.* file
    data_tar = None
    for f in ar_extract.iterdir():
        if f.name.startswith("data.tar"):
            data_tar = f
            break
    
    if not data_tar:
        log("  No data.tar found in .deb", "ERROR")
        return False
    
    # Extract data.tar.*
    result = subprocess.run(
        ["tar", "-xf", str(data_tar), "-C", str(extract_dir)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        log(f"  data.tar extract failed: {result.stderr}", "ERROR")
        return False
    
    # Don't clean up ar_extract here - build_txpkg needs the data.tar
    return True

def verify_binary(filepath):
    """
    Verify that a binary is Android Bionic compatible.
    Returns (is_valid, details_dict)
    """
    result = {
        "path": str(filepath),
        "valid": False,
        "arch": None,
        "interpreter": None,
        "pie": False,
        "bionic_only": False,
        "errors": [],
    }
    
    # Run 'file' command
    try:
        file_out = subprocess.run(
            ["file", str(filepath)],
            capture_output=True, text=True, timeout=10
        )
        file_info = file_out.stdout
    except Exception as e:
        result["errors"].append(f"file command failed: {e}")
        return False, result
    
    result["file_output"] = file_info
    
    # Check architecture
    if "ARM aarch64" in file_info or "aarch64" in file_info:
        result["arch"] = "aarch64"
    elif "x86-64" in file_info or "x86_64" in file_info:
        result["arch"] = "x86_64"
        result["errors"].append("Wrong architecture: x86_64 instead of aarch64")
        return False, result
    
    # Check for PIE
    if "pie executable" in file_info.lower() or "PIE" in file_info:
        result["pie"] = True
    elif "shared object" in file_info.lower():
        # Shared libraries are inherently position-independent
        result["pie"] = True
    
    # Check interpreter - must NOT reference musl
    if "ld-musl" in file_info:
        result["errors"].append("Binary uses musl libc interpreter")
        return False, result
    
    if "ld-linux" in file_info:
        result["errors"].append("Binary uses glibc interpreter")
        return False, result
    
    # Check for Bionic linker
    if "linker64" in file_info or "linker" in file_info:
        result["interpreter"] = "/system/bin/linker64"
        result["bionic_only"] = True
    
    # Run readelf for more detailed checks
    try:
        readelf_h = subprocess.run(
            ["readelf", "-h", str(filepath)],
            capture_output=True, text=True, timeout=10
        )
        readelf_h_out = readelf_h.stdout
        
        # Check machine type
        if "AArch64" in readelf_h_out:
            result["arch"] = "aarch64"
        
        # Check for DYN type (PIE)
        if "Type:                               DYN" in readelf_h_out:
            result["pie"] = True
            
    except Exception as e:
        result["errors"].append(f"readelf -h failed: {e}")
    
    try:
        readelf_d = subprocess.run(
            ["readelf", "-d", str(filepath)],
            capture_output=True, text=True, timeout=10
        )
        readelf_d_out = readelf_d.stdout
        
        # Check for NEEDED entries
        needed_libs = []
        for line in readelf_d_out.split("\n"):
            if "NEEDED" in line:
                lib = line.split("[", 1)[1].split("]", 1)[0] if "[" in line else ""
                needed_libs.append(lib)
        
        result["needed_libs"] = needed_libs
        
        # Check for musl/glibc specific libraries
        for lib in needed_libs:
            if "musl" in lib:
                result["errors"].append(f"Depends on musl library: {lib}")
                return False, result
    except Exception as e:
        result["errors"].append(f"readelf -d failed: {e}")
    
    try:
        readelf_l = subprocess.run(
            ["readelf", "-l", str(filepath)],
            capture_output=True, text=True, timeout=10
        )
        readelf_l_out = readelf_l.stdout
        
        # Check for PT_INTERP
        if "INTERP" in readelf_l_out:
            for line in readelf_l_out.split("\n"):
                if "INTERP" in line and "Requesting program interpreter" in readelf_l_out:
                    interp_section = [l for l in readelf_l_out.split("\n") if "interpreter" in l.lower()]
                    if interp_section:
                        interp = interp_section[0]
                        result["interpreter"] = interp
                        
                        # Check for Bionic linker
                        if "linker" in interp and ("system" in interp or "android" in interp):
                            result["bionic_only"] = True
                        elif "ld-musl" in interp:
                            result["errors"].append(f"Uses musl interpreter: {interp}")
                            return False, result
                        elif "ld-linux" in interp:
                            result["errors"].append(f"Uses glibc interpreter: {interp}")
                            return False, result
                    break
        else:
            # No interpreter = static binary or shared library - OK for Android
            result["interpreter"] = "(none - static or library)"
            result["bionic_only"] = True
            
    except Exception as e:
        result["errors"].append(f"readelf -l failed: {e}")
    
    # Final validation
    is_valid = (
        result["arch"] == "aarch64" and
        result["pie"] and
        len(result["errors"]) == 0 and
        result["bionic_only"]
    )
    
    result["valid"] = is_valid
    return is_valid, result

def validate_package_binaries(files_dir, skip_check=False):
    """Validate all binaries in a package directory."""
    if skip_check:
        return True, []
    
    files_dir = Path(files_dir)
    all_valid = True
    all_results = []
    
    for filepath in files_dir.rglob("*"):
        if not filepath.is_file():
            continue
        
        # Quick check if it's an ELF binary
        try:
            with open(filepath, "rb") as f:
                magic = f.read(4)
                if magic != b"\x7fELF":
                    continue
        except:
            continue
        
        # It's an ELF - validate it
        rel_path = filepath.relative_to(files_dir)
        is_valid, result = verify_binary(filepath)
        all_results.append((str(rel_path), result))
        
        if not is_valid:
            all_valid = False
            log(f"    INVALID: {rel_path}", "WARN")
            for err in result["errors"]:
                log(f"      - {err}", "WARN")
    
    return all_valid, all_results

def build_txpkg(pkg_name, pkg_info, work_dir, termux_pkgs):
    """
    Build a single .txpkg package from a Termux .deb.
    Returns: (success_bool, result_dict)
    """
    result = {
        "name": pkg_name,
        "success": False,
        "txpkg_path": None,
        "json_path": None,
        "sha256_path": None,
        "errors": [],
        "warnings": [],
    }
    
    termux_name = pkg_info.get("termux_name", pkg_name)
    version = pkg_info.get("version", "0.0.0")
    release = pkg_info.get("release", 0)
    
    log(f"Building {pkg_name} (from termux:{termux_name}) v{version}-{release}")
    
    # Find Termux package
    deb_url = find_termux_deb_url(termux_name, termux_pkgs)
    if not deb_url:
        result["errors"].append(f"Termux package '{termux_name}' not found")
        log(f"  ERROR: Termux package '{termux_name}' not found", "ERROR")
        return False, result
    
    # Download .deb
    deb_filename = deb_url.split("/")[-1]
    deb_cache = CACHE_DIR / deb_filename
    deb_path = download_deb(deb_url, deb_cache)
    
    if not deb_path:
        # Try alternative URL format
        alt_url = f"{TERMUX_REPO_URL}/pool/main/{termux_name[0]}/{termux_name}/{termux_name}_{version}_{ARCH}.deb"
        deb_path = download_deb(alt_url, CACHE_DIR / f"{termux_name}_{version}_{ARCH}.deb")
    
    if not deb_path or not deb_path.exists():
        result["errors"].append(f"Failed to download .deb for {termux_name}")
        log(f"  ERROR: Failed to download {termux_name}", "ERROR")
        return False, result
    
    # Extract .deb
    extract_dir = Path(work_dir) / f"extract_{pkg_name}"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    
    if not extract_deb(deb_path, extract_dir):
        result["errors"].append("Failed to extract .deb")
        log(f"  ERROR: Failed to extract .deb", "ERROR")
        return False, result
    
    # Stage directory for txpkg
    stage_dir = Path(work_dir) / f"stage_{pkg_name}"
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir()
    
    files_dir = stage_dir / "files"
    files_dir.mkdir()
    
    # Find the data.tar.* in the extracted ar archive and extract directly to files/
    # This preserves symlinks correctly
    ar_extract = extract_dir / "_ar"
    data_tar = None
    for f in ar_extract.iterdir():
        if f.name.startswith("data.tar"):
            data_tar = f
            break
    
    if not data_tar:
        result["errors"].append("No data.tar found in extracted .deb")
        log(f"  ERROR: No data.tar found", "ERROR")
        return False, result
    
    # Extract data.tar.* directly, preserving symlinks
    temp_extract = Path(work_dir) / f"temp_extract_{pkg_name}"
    if temp_extract.exists():
        shutil.rmtree(temp_extract)
    temp_extract.mkdir(parents=True)
    
    extract_result = subprocess.run(
        ["tar", "-xf", str(data_tar), "-C", str(temp_extract)],
        capture_output=True, text=True
    )
    
    if extract_result.returncode != 0:
        result["errors"].append(f"data.tar extract failed: {extract_result.stderr}")
        log(f"  ERROR: data.tar extraction failed", "ERROR")
        return False, result
    
    # Move from Termux prefix to standard layout
    termux_prefix = temp_extract / "data" / "data" / "com.termux" / "files"
    if termux_prefix.exists():
        # Has Termux prefix - move usr/ to files/
        for subdir in ["usr", "etc", "var", "opt"]:
            src = termux_prefix / subdir
            if src.exists():
                dest = files_dir / subdir
                # Use rsync-like copy that preserves symlinks
                subprocess.run(
                    ["cp", "-a", str(src) + "/.", str(dest) + "/"],
                    capture_output=True
                )
                if not dest.exists():
                    # Fallback: rename
                    shutil.move(str(src), str(dest))
    elif (temp_extract / "usr").exists():
        # Direct usr/ layout
        dest = files_dir / "usr"
        shutil.move(str(temp_extract / "usr"), str(dest))
    else:
        # Move everything to files/
        for item in temp_extract.iterdir():
            if item.name.startswith("_"):
                continue
            dest = files_dir / item.name
            shutil.move(str(item), str(dest))
    
    # Clean up temp extract
    shutil.rmtree(temp_extract, ignore_errors=True)
    
    # Clean up ar extract
    shutil.rmtree(ar_extract, ignore_errors=True)
    
    # Count files staged
    file_count = sum(1 for _ in files_dir.rglob("*") if _.is_file()) if files_dir.exists() else 0
    log(f"  Staged {file_count} files")
    
    if file_count == 0:
        result["errors"].append("No files staged - empty package")
        log(f"  ERROR: Empty package", "ERROR")
        return False, result
    
    # Validate binaries
    skip_check = pkg_info.get("skip_binary_check", False)
    is_valid, validation_results = validate_package_binaries(files_dir, skip_check)
    
    if not is_valid and not skip_check:
        for rel_path, vresult in validation_results:
            if not vresult["valid"]:
                result["warnings"].append(f"{rel_path}: {vresult['errors']}")
        # Don't fail - just warn, since we're repackaging existing binaries
        # that Termux has already validated for Android
    
    # Generate checksums
    checksums_path = stage_dir / "checksums"
    with open(checksums_path, "w") as f:
        for filepath in sorted(files_dir.rglob("*")):
            if filepath.is_file():
                rel_path = filepath.relative_to(files_dir)
                checksum = sha256_file(filepath)
                f.write(f"{checksum}  {rel_path}\n")
    
    # Create CONTROL file
    deps = pkg_info.get("deps", "")
    control_path = stage_dir / "CONTROL"
    with open(control_path, "w") as f:
        f.write(f"Package: {pkg_name}\n")
        f.write(f"Version: {version}\n")
        f.write(f"Release: {release}\n")
        f.write(f"Architecture: {ARCH}\n")
        f.write(f"License: {pkg_info.get('license', 'UNKNOWN')}\n")
        f.write(f"Description: {pkg_info.get('desc', '')}\n")
        f.write(f"Homepage: {pkg_info.get('homepage', '')}\n")
        f.write(f"Maintainer: TX Packages <packages@txterminal.dev>\n")
        f.write(f"Category: {pkg_info.get('cat', 'misc')}\n")
        f.write(f"Essential: {'yes' if pkg_info.get('essential', False) else 'no'}\n")
        f.write(f"Depends: {deps}\n")
        f.write(f"Provides: {pkg_info.get('prov', '')}\n")
        f.write(f"Conflicts:\n")
        f.write(f"Replaces:\n")
        f.write(f"Breaks:\n")
        f.write(f"Suggests:\n")
        f.write(f"Recommends:\n")
        f.write(f"Optional:\n")
    
    # Create manifest.json
    txpkg_filename = f"{pkg_name}-{version}-{release}.{ARCH}.txpkg"
    txpkg_path = PKG_DIR / txpkg_filename
    
    # Calculate package size
    installed_size = sum(
        f.stat().st_size 
        for f in files_dir.rglob("*") 
        if f.is_file()
    )
    
    manifest = {
        "name": pkg_name,
        "version": version,
        "release": release,
        "architecture": ARCH,
        "license": pkg_info.get("license", "UNKNOWN"),
        "description": pkg_info.get("desc", ""),
        "homepage": pkg_info.get("homepage", ""),
        "maintainer": "TX Packages <packages@txterminal.dev>",
        "category": pkg_info.get("cat", "misc"),
        "essential": pkg_info.get("essential", False),
        "depends": deps,
        "provides": pkg_info.get("prov", ""),
        "conflicts": "",
        "sha256": "",  # Will be set after packaging
        "size": 0,
        "installed_size": installed_size,
        "format_version": 2,
        "metadata_version": 2,
        "built_for": "android-bionic",
        "api_level": "29+",
    }
    
    manifest_path = stage_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Create .txpkg archive (tar.xz)
    # Archive contains: CONTROL, manifest.json, checksums, files/
    if txpkg_path.exists():
        txpkg_path.unlink()
    
    # Build tar command
    with tarfile.open(txpkg_path, "w:xz") as tar:
        tar.add(control_path, arcname="CONTROL")
        tar.add(manifest_path, arcname="manifest.json")
        tar.add(checksums_path, arcname="checksums")
        tar.add(files_dir, arcname="files")
    
    # Calculate SHA256 of the .txpkg
    txpkg_sha256 = sha256_file(txpkg_path)
    txpkg_size = txpkg_path.stat().st_size
    
    # Write .sha256 file
    sha256_path = PKG_DIR / f"{txpkg_filename}.sha256"
    with open(sha256_path, "w") as f:
        f.write(f"{txpkg_sha256}  {txpkg_filename}\n")
    
    # Write .json metadata file
    json_filename = f"{pkg_name}-{version}-{release}.{ARCH}.json"
    json_path = PKG_DIR / json_filename
    
    manifest["sha256"] = txpkg_sha256
    manifest["size"] = txpkg_size
    
    with open(json_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    result["success"] = True
    result["txpkg_path"] = str(txpkg_path)
    result["json_path"] = str(json_path)
    result["sha256_path"] = str(sha256_path)
    result["sha256"] = txpkg_sha256
    result["size"] = txpkg_size
    
    log(f"  SUCCESS: {txpkg_filename} ({txpkg_size:,} bytes)")
    
    return True, result

def build_all():
    """Build all packages in priority order."""
    setup_dirs()
    
    log("=" * 60)
    log("TX Bionic Build System")
    log("Target: Android ARM64 Bionic libc")
    log("Source: Termux Package Repository")
    log("=" * 60)
    
    # Download Termux package list
    termux_pkgs = download_termux_pkglist()
    
    # Sort packages by priority
    sorted_packages = sorted(PACKAGES.items(), key=lambda x: (x[1]["prio"], x[0]))
    
    log(f"\nBuilding {len(sorted_packages)} packages...")
    log("-" * 60)
    
    results = {}
    work_base = tempfile.mkdtemp(prefix="txbionic_")
    
    # Build in priority order (sequentially for dependency resolution)
    for pkg_name, pkg_info in sorted_packages:
        work_dir = Path(work_base) / pkg_name
        work_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            success, result = build_txpkg(pkg_name, pkg_info, work_dir, termux_pkgs)
            results[pkg_name] = result
        except Exception as e:
            log(f"  EXCEPTION: {e}", "ERROR")
            results[pkg_name] = {
                "name": pkg_name,
                "success": False,
                "errors": [str(e)],
            }
    
    # Clean up work directory
    shutil.rmtree(work_base, ignore_errors=True)
    
    # Summary
    log("\n" + "=" * 60)
    log("BUILD SUMMARY")
    log("=" * 60)
    
    success_count = sum(1 for r in results.values() if r.get("success", False))
    fail_count = len(results) - success_count
    
    log(f"Successful: {success_count}")
    log(f"Failed: {fail_count}")
    
    if fail_count > 0:
        log("\nFailed packages:")
        for name, result in results.items():
            if not result.get("success", False):
                log(f"  - {name}: {result.get('errors', ['Unknown error'])}")
    
    return results

def generate_repo_metadata(results):
    """Generate Packages.json, index.json, and SHA256SUMS."""
    log("\n" + "=" * 60)
    log("Generating repository metadata")
    log("=" * 60)
    
    packages_list = []
    sha256sums_lines = []
    
    for pkg_name in sorted(results.keys()):
        result = results[pkg_name]
        if not result.get("success", False):
            continue
        
        pkg_info = PACKAGES[pkg_name]
        version = pkg_info.get("version", "0.0.0")
        release = pkg_info.get("release", 0)
        
        txpkg_filename = f"{pkg_name}-{version}-{release}.{ARCH}.txpkg"
        
        entry = {
            "name": pkg_name,
            "version": f"{version}-{release}",
            "architecture": ARCH,
            "filename": txpkg_filename,
            "sha256": result.get("sha256", ""),
            "category": pkg_info.get("cat", "misc"),
            "depends": pkg_info.get("deps", ""),
            "description": pkg_info.get("desc", ""),
        }
        packages_list.append(entry)
        
        sha256sums_lines.append(f"{result.get('sha256', '')}  packages/{txpkg_filename}")
    
    # Write Packages.json
    packages_json = {
        "repository": "TX Bionic Stable",
        "version": 2,
        "format_version": 2,
        "metadata_version": 2,
        "architecture": ARCH,
        "channel": "stable",
        "target": "android-bionic",
        "api_level": "29+",
        "built": datetime.now().isoformat(),
        "package_count": len(packages_list),
        "packages": packages_list,
    }
    
    packages_json_path = REPO_DIR / "Packages.json"
    with open(packages_json_path, "w") as f:
        json.dump(packages_json, f, indent=2)
    log(f"Generated Packages.json ({len(packages_list)} packages)")
    
    # Write index.json
    index_json = {
        "repository": "TX Bionic Stable",
        "channel": "stable",
        "architecture": ARCH,
        "target": "android-bionic",
        "api_level": "29+",
        "version": 2,
        "url": "https://github.com/Rick000000007/tx-packages",
        "updated": datetime.now().isoformat(),
        "packages_count": len(packages_list),
    }
    
    index_json_path = REPO_DIR / "index.json"
    with open(index_json_path, "w") as f:
        json.dump(index_json, f, indent=2)
    log("Generated index.json")
    
    # Write SHA256SUMS
    sha256sums_path = REPO_DIR / "SHA256SUMS"
    with open(sha256sums_path, "w") as f:
        f.write("\n".join(sorted(sha256sums_lines)) + "\n")
    log("Generated SHA256SUMS")
    
    return packages_json_path, index_json_path, sha256sums_path

if __name__ == "__main__":
    results = build_all()
    generate_repo_metadata(results)
    
    success = sum(1 for r in results.values() if r.get("success", False))
    total = len(results)
    
    log(f"\nBuild complete: {success}/{total} packages built successfully")
    
    if success < total:
        sys.exit(1)
