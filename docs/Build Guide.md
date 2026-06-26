# TX Package Build Guide

## Overview

This guide explains how to build TX Packages from source using the provided build system. The build system downloads Alpine Linux aarch64 packages and repackages them into the `.txpkg` format.

## Prerequisites

- Python 3.8+
- Network access to Alpine Linux package mirrors
- At least 500 MB free disk space

## Quick Start

### Building All Packages

```bash
cd tx-packages
python3 build/build_final.py
```

This will:
1. Download Alpine Linux aarch64 APK packages
2. Convert them to `.txpkg` format
3. Generate repository metadata
4. Output everything to `repo/stable/`

### Building a Single Package

```python
from build.build_final import build_package
import tempfile
from pathlib import Path

pkg_info = {
    "version": "7.2", "release": 1,
    "alpine_pkg": "nano", "desc": "Lightweight terminal text editor",
    "license": "GPL-3.0+", "cat": "editors",
    "deps": "musl ncurses-libs ncurses-terminfo",
    "prov": "editor", "prio": 3
}

work_dir = Path(tempfile.mkdtemp())
result = build_package("nano", pkg_info, work_dir)
print(result)
```

## Build System Architecture

### Package Definitions

Packages are defined in `build/build_final.py` in the `PACKAGES` dictionary:

```python
PACKAGES = {
    "nano": {
        "version": "7.2",           # Alpine package version
        "release": 1,               # Alpine package release
        "alpine_pkg": "nano",      # Alpine package name
        "desc": "...",             # Package description
        "license": "GPL-3.0+",     # SPDX license identifier
        "cat": "editors",          # Package category
        "deps": "musl ncurses-libs",  # TX package dependencies
        "prov": "editor",          # Virtual packages provided
        "prio": 3,                 # Build priority (dependency order)
    },
}
```

### Dependency Resolution

Packages are built in priority order (lowest first). The build system uses:

- **Priority 0**: Base libraries (musl, libgcc, attr)
- **Priority 1**: Core libraries (zlib, pcre2, gmp)
- **Priority 2**: Higher-level libraries and basic tools
- **Priority 3**: Applications and complex tools
- **Priority 4**: Network tools with many dependencies

### Build Process

For each package, the build system:

1. **Download**: Fetches the Alpine APK from `dl-cdn.alpinelinux.org`
2. **Extract**: Decompresses the gzip-compressed tar archive
3. **Stage**: Copies files to the `files/` directory with proper layout
4. **Metadata**: Creates CONTROL, manifest.json, and checksums files
5. **Archive**: Packs everything into a `.txpkg` tar.xz archive
6. **Hash**: Computes SHA-256 checksums for verification

## Adding a New Package

### Step 1: Find the Alpine Package

Search Alpine's package index:

```bash
curl -s "https://pkgs.alpinelinux.org/packages" | grep <package-name>
```

Or browse: https://pkgs.alpinelinux.org/packages

### Step 2: Verify Architecture

Ensure the package is available for `aarch64`:

```bash
curl -s "https://dl-cdn.alpinelinux.org/alpine/v3.19/main/aarch64/APKINDEX.tar.gz" | \
  tar -xz -O APKINDEX | grep -A1 "^P:<package-name>$"
```

### Step 3: Add Package Definition

Add an entry to the `PACKAGES` dictionary:

```python
"my-package": {
    "version": "1.0.0",         # From Alpine
    "release": 0,               # From Alpine (without the 'r' prefix)
    "alpine_pkg": "my-package", # Alpine package name
    "desc": "Short description",
    "license": "MIT",
    "cat": "utils",
    "deps": "musl zlib",       # Comma-separated TX package names
    "prov": "",                # Virtual packages provided
    "prio": 2,                 # Build priority
}
```

### Step 4: Resolve Dependencies

Ensure all dependencies:
- Exist in the `PACKAGES` dictionary
- Have lower or equal priority
- Form no circular dependencies

### Step 5: Build and Test

```bash
python3 build/build_final.py
```

### Step 6: Validate

```bash
python3 build/validate-repo.py
```

## Build Outputs

After building, the following files are generated:

```
repo/stable/packages/
|-- <name>-<ver>-<rel>.aarch64.txpkg       # Package archive
|-- <name>-<ver>-<rel>.aarch64.json         # Package metadata
`-- <name>-<ver>-<rel>.aarch64.txpkg.sha256 # Checksum

repo/stable/
|-- Packages.json    # Package catalog (all packages)
|-- index.json       # Repository metadata
`-- SHA256SUMS       # All package checksums
```

## Custom Builds

### Using a Different Alpine Version

Edit `ALPINE_VERSION` in `build/build_final.py`:

```python
ALPINE_VERSION = "v3.20"  # Or newer
```

### Custom Alpine Mirror

Edit `ALPINE_MIRROR` in `build/build_final.py`:

```python
ALPINE_MIRROR = "https://mirror.example.com/alpine"
```

### Building from Source Instead of Alpine

For packages that need custom compilation:

1. Create a custom build script in `build/packages/<name>/`
2. Compile for Android aarch64 using the Android NDK
3. Stage files to the proper `files/` layout
4. Generate CONTROL, manifest.json, and checksums
5. Create the `.txpkg` archive

Example custom build script:

```bash
#!/bin/bash
# build/packages/myapp/build.sh

set -e
PKG_NAME="myapp"
VERSION="1.0.0"
RELEASE="1"
ARCH="aarch64"

# Build directory
BUILD_DIR="build/packages/myapp"
STAGE_DIR="$BUILD_DIR/stage"
FILES_DIR="$STAGE_DIR/files"

# Clean and create directories
rm -rf "$STAGE_DIR"
mkdir -p "$FILES_DIR/usr/bin"

# Compile (example)
$CC -o "$FILES_DIR/usr/bin/myapp" src/main.c

# Create CONTROL
cat > "$STAGE_DIR/CONTROL" <<EOF
Package: $PKG_NAME
Version: $VERSION
Release: $RELEASE
Architecture: $ARCH
...
EOF

# Create checksums
cd "$FILES_DIR"
find . -type f -exec sha256sum {} \; > "$STAGE_DIR/checksumsums"

# Create .txpkg
cd "$STAGE_DIR"
tar -cJf "../../../repo/stable/packages/${PKG_NAME}-${VERSION}-${RELEASE}.${ARCH}.txpkg" \
  CONTROL manifest.json checksums files/
```

## Reproducible Builds

To ensure reproducible builds:

1. Pin the Alpine version (`ALPINE_VERSION`)
2. Use a specific mirror (`ALPINE_MIRROR`)
3. Pin package versions in `PACKAGES`
4. Clear the cache before building: `rm -rf build/.cache/`

## Troubleshooting

### Download Failures

If a package fails to download:
- Check the Alpine package exists for the specified version
- Verify network connectivity to `dl-cdn.alpinelinux.org`
- Try a different Alpine mirror
- Check the package name matches exactly (case-sensitive)

### Circular Dependencies

The build system validates the dependency graph. If a cycle is detected:
- Review the `depends` field of packages in the cycle
- Break the cycle by removing or reordering dependencies
- Ensure no package depends (directly or transitively) on itself

### Empty Packages

If a package has 0 files:
- The Alpine APK may be a meta-package
- The APK extraction may have failed
- Check the extracted contents in the temporary build directory

## Advanced Configuration

### Parallel Builds

The build system uses 8 concurrent workers by default. Adjust:

```python
MAX_WORKERS = 16  # In build/build_final.py
```

### Cache Directory

Downloaded APKs are cached in `build/.cache/`. To force re-download:

```bash
rm -rf build/.cache/
```

### Logging

For verbose output during builds, set:

```bash
export TX_BUILD_DEBUG=1
```
