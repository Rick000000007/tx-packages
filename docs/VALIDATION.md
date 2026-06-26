# TX Bionic Package Validation Guide

How to validate packages for Android Bionic compatibility.

## Overview

Every package in the TX Bionic repository must pass strict validation before inclusion. This ensures all binaries are native Android ARM64 executables linked against Bionic libc only.

## Validation Rules

### Binary Requirements

| Check | Requirement | Failure |
|-------|-------------|---------|
| Architecture | Must be `AArch64` (ARM64) | Binary won't run on ARM64 |
| PIE | Must be position-independent | Android security policy violation |
| Interpreter | Must be `/system/bin/linker64` | Wrong dynamic linker |
| libc | Must be Bionic | Runtime errors with wrong libc |
| No musl | Must NOT reference `ld-musl-*` | Missing interpreter error |
| No glibc | Must NOT reference `ld-linux-*` | Missing interpreter error |

### Package Format Requirements

| Check | Requirement |
|-------|-------------|
| Archive format | tar.xz |
| Required files | CONTROL, manifest.json, checksums |
| Payload layout | files/usr/ (consistent prefix) |
| No mixed layouts | Cannot use both files/bin/ and files/usr/bin/ |

## Running Validation

### Validate Entire Repository

```bash
./build.sh validate
```

Output:
```
[PASS] attr-2.5.1-0.aarch64.txpkg       (0/0 binaries OK)
[PASS] zlib-1.3.1-0.aarch64.txpkg        (3/3 binaries OK)
[PASS] curl-8.11.1-0.aarch64.txpkg       (2/2 binaries OK)
...
```

### Validate Specific Checks

#### Check Architecture

```bash
file files/usr/bin/program
```

Must show: `ARM aarch64`

Must NOT show: `x86-64`, `Intel 80386`, `ARM EABI5` (32-bit)

#### Check PIE

```bash
readelf -h files/usr/bin/program | grep Type
```

Must show: `DYN (Position-Independent Executable file)`

#### Check Interpreter

```bash
readelf -l files/usr/bin/program | grep interpreter
```

Must show: `/system/bin/linker64`

Must NOT show: `/lib/ld-musl-aarch64.so.1`, `/lib64/ld-linux-aarch64.so.1`

#### Check Dependencies

```bash
readelf -d files/usr/bin/program | grep NEEDED
```

Must NOT show any `musl` or `glibc` libraries.

### Using objdump

```bash
objdump -p files/usr/bin/program | grep NEEDED
```

All needed libraries must be either:
- Android Bionic: `libc.so`, `libm.so`, `libdl.so`
- Or libraries in the TX repository

## Manual Validation Example

```bash
# Extract a .txpkg
mkdir -p /tmp/validate
tar -xf repo/stable/packages/curl-8.11.1-0.aarch64.txpkg -C /tmp/validate

# Check the binary
cd /tmp/validate

# 1. Architecture and type
file files/usr/bin/curl
# Expected: ELF 64-bit LSB pie executable, ARM aarch64

# 2. ELF header
readelf -h files/usr/bin/curl
# Check: Machine = AArch64
# Check: Type = DYN (PIE)

# 3. Program interpreter
readelf -l files/usr/bin/curl | grep -A2 INTERP
# Expected: /system/bin/linker64

# 4. Dynamic dependencies
readelf -d files/usr/bin/curl | grep NEEDED
# Expected: libcurl.so, libssl.so, libcrypto.so, etc.
# Forbidden: ld-musl-aarch64.so.1, libc.so.6

# 5. objdump
objdump -p files/usr/bin/curl | grep NEEDED

# 6. Check all binaries in package
find files -type f | while read f; do
    magic=$(xxxd -l 4 "$f" | head -1)
    if [ "$magic" = "0000000: 7f45 4c46" ]; then
        echo "=== $f ==="
        file "$f"
        readelf -l "$f" 2>/dev/null | grep interpreter || true
    fi
done

# Clean up
rm -rf /tmp/validate
```

## Automated Validation in Build System

The build system automatically validates every binary during the build process. Invalid binaries are rejected.

### Validation Bypass (Development Only)

For data-only packages (no binaries), set in package definition:

```python
"skip_binary_check": True
```

Examples: `ca-certificates-bundle`, `ndk-sysroot` (headers only)

## Validation Failure Examples

### musl Binary (REJECTED)

```bash
$ file curl
curl: ELF 64-bit LSB pie executable, ARM aarch64, version 1 (SYSV), 
      dynamically linked, interpreter /lib/ld-musl-aarch64.so.1, ...

# Result: REJECTED - uses musl interpreter
```

### glibc Binary (REJECTED)

```bash
$ file curl
curl: ELF 64-bit LSB executable, ARM aarch64, version 1 (SYSV),
      dynamically linked, interpreter /lib64/ld-linux-aarch64.so.1, ...

# Result: REJECTED - uses glibc interpreter and not PIE
```

### Correct Bionic Binary (ACCEPTED)

```bash
$ file curl
curl: ELF 64-bit LSB pie executable, ARM aarch64, version 1 (SYSV),
      dynamically linked, interpreter /system/bin/linker64, ...

# Result: ACCEPTED - Bionic PIE executable
```

## CI/CD Integration

Add validation to your CI pipeline:

```yaml
# .github/workflows/validate.yml
name: Validate Packages

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y binutils python3
      
      - name: Validate repository
        run: |
          ./build.sh validate
```

## Acceptance Criteria

A package is accepted when:

- [ ] All binaries are AArch64
- [ ] All binaries are PIE
- [ ] All binaries use `/system/bin/linker64`
- [ ] No references to musl
- [ ] No references to glibc
- [ ] Package format is valid tar.xz
- [ ] Contains CONTROL, manifest.json, checksums
- [ ] Uses consistent `files/usr/` layout
- [ ] SHA-256 checksums match
- [ ] Metadata is complete
