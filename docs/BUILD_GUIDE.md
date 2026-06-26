# TX Bionic Build Guide

Comprehensive guide for building packages from source using the Android NDK.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [NDK Environment Setup](#ndk-environment-setup)
5. [Build System Reference](#build-system-reference)
6. [Package Definitions](#package-definitions)
7. [Dependency Management](#dependency-management)
8. [Building Individual Packages](#building-individual-packages)
9. [Adding New Packages](#adding-new-packages)
10. [Troubleshooting](#troubleshooting)

## Overview

The TX Bionic build system supports two build modes:

1. **Termux Repackage Mode** (default): Downloads pre-built Termux packages and repackages them as `.txpkg`
2. **NDK Source Build Mode**: Compiles packages from source using the Android NDK

Most packages use Mode 1 for efficiency. Mode 2 is used for:
- Packages not available in Termux
- Custom patched packages
- Packages requiring specific configure options
- Updates when Termux packages are outdated

## Prerequisites

### Required

- Python 3.8 or newer
- Linux x86_64 build host (or WSL on Windows)
- 10+ GB free disk space
- Internet access for downloading packages

### Required for Source Builds

- Android NDK r25c or newer
- Standard build tools: `make`, `autoconf`, `automake`, `libtool`, `m4`
- `curl` for downloading sources
- `tar`, `gzip`, `bzip2`, `xz` for archive extraction

### Optional

- `ccache` for faster rebuilds
- `ninja-build` for meson-based projects
- `cmake` 3.18+ for cmake-based projects

## Quick Start

### Full Repository Build

```bash
# Clone the repository
git clone https://github.com/Rick000000007/tx-packages.git
cd tx-packages

# Build everything (Termux repackage mode)
./build.sh all

# Validate the output
./build.sh validate
```

### Build with NDK

```bash
# Set up NDK environment
export ANDROID_NDK=/opt/android-ndk-r27c
export API_LEVEL=29

# Verify NDK setup
./build.sh ndk-setup

# Build specific package from source
cd build/ndk-scripts
./01_zlib.sh
```

## NDK Environment Setup

### Downloading the Android NDK

**Option 1: Direct Download**

```bash
wget https://dl.google.com/android/repository/android-ndk-r27c-linux.zip
unzip android-ndk-r27c-linux.zip
sudo mv android-ndk-r27c /opt/
export ANDROID_NDK=/opt/android-ndk-r27c
```

**Option 2: Via Android Studio SDK Manager**

1. Open Android Studio
2. Tools -> SDK Manager
3. SDK Tools tab
4. Check "NDK (Side by side)"
5. Apply

**Option 3: Via sdkmanager Command Line**

```bash
sdkmanager "ndk;27.0.12077973"
export ANDROID_NDK=$ANDROID_SDK/ndk/27.0.12077973
```

### NDK Environment Variables

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Android NDK
export ANDROID_NDK=/opt/android-ndk-r27c
export API_LEVEL=29

# Optional: Add to PATH
export PATH=$ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH
```

### Verify NDK Installation

```bash
./build.sh ndk-setup
```

Expected output:
```
NDK: /opt/android-ndk-r27c
API: 29
ARCH: aarch64
  CC: /opt/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android29-clang
  CXX: /opt/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android29-clang++
  ...
Toolchain verified. Ready to build.
```

## Build System Reference

### Build Commands

| Command | Description |
|---------|-------------|
| `./build.sh all` | Build all packages and generate metadata |
| `./build.sh pkg <name>` | Build a single package |
| `./build.sh validate` | Validate all packages |
| `./build.sh clean` | Remove build cache |
| `./build.sh metadata` | Generate repository metadata only |
| `./build.sh ndk-setup` | Verify NDK installation |
| `./build.sh help` | Show help |

### Build Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ANDROID_NDK` | - | Path to Android NDK (required for source builds) |
| `API_LEVEL` | `29` | Target Android API level |
| `JOBS` | `$(nproc)` | Number of parallel build jobs |
| `BUILD_ROOT` | `./build-root` | Build output directory |
| `CCACHE_DIR` | - | ccache directory for faster rebuilds |

### Build Output Structure

```
build-root/
├── src/                    # Downloaded source code
├── stage/<pkg>/            # Staging directory per package
│   ├── CONTROL             # Package control file
│   ├── manifest.json       # JSON metadata
│   ├── checksums           # SHA-256 checksums
│   └── files/              # Package payload
│       └── usr/            # Installation prefix
├── out/                    # Built .txpkg files
└── logs/                   # Build logs
```

## Package Definitions

Packages are defined in `build/packages.py` in the `PACKAGES` dictionary:

```python
"curl": {
    "termux_name": "curl",           # Termux package name
    "version": "8.11.1",             # Package version
    "release": 0,                     # Package release
    "desc": "Command-line tool...",   # Description
    "license": "curl",               # SPDX license
    "cat": "network",                # Category
    "deps": "ndk-sysroot openssl...", # Dependencies (space-separated)
    "prov": "",                      # Virtual packages provided
    "prio": 4,                       # Build priority (dependency order)
    "homepage": "https://curl.se/",  # Project URL
    "skip_binary_check": False,      # Skip binary validation (for data-only pkgs)
}
```

### Build Priority Levels

| Priority | Description | Examples |
|----------|-------------|----------|
| 0 | Base libraries with no deps | ndk-sysroot, zlib, gmp |
| 1 | Core libraries | openssl, libedit, readline |
| 2 | Higher-level libraries | libmagic, libssh2 |
| 3 | Applications and tools | coreutils, nano, curl |
| 4 | Complex network tools | curl, openssh-client |

## Dependency Management

### Dependency Rules

1. **Bionic is implicit**: The Android system provides Bionic libc, so packages do NOT depend on a `libc` or `musl` package
2. **NDK libraries**: Packages needing compiler-rt or libc++ depend on `ndk-sysroot`
3. **Library packages**: Binary packages depend on their library packages
4. **Virtual packages**: Use `provides` for virtual packages (e.g., `pkgconf` provides `pkg-config`)

### Dependency Translation from musl-based repo

| Old (musl) | New (Bionic) | Notes |
|------------|--------------|-------|
| `musl` | `ndk-sysroot` | Bionic is always present |
| `libgcc` | `libgcc` | Now maps to `libcompiler-rt` |
| `libstdc++` | `libstdc++` | Now maps to NDK's `libc++` |
| `musl ncurses-libs` | `ndk-sysroot ncurses-libs` | Replace musl with ndk-sysroot |

## Building Individual Packages

### Method 1: Termux Repackage (Default)

```bash
./build.sh pkg curl
```

This will:
1. Download the Termux `curl` .deb package
2. Extract it
3. Transform paths from Termux prefix to TX layout
4. Create .txpkg with updated metadata
5. Validate the binary

### Method 2: NDK Source Build

For packages requiring custom compilation:

```bash
# Set up environment
export ANDROID_NDK=/opt/android-ndk-r27c
export API_LEVEL=29

# Run the NDK build script
cd build/ndk-scripts
./01_zlib.sh
```

### Writing Custom NDK Build Scripts

Template:

```bash
#!/bin/bash
set -e

PKG_NAME="my-package"
VERSION="1.0.0"
RELEASE="0"
ARCH="aarch64"
API="${API:-29}"

# NDK toolchain
: "${NDK:=${ANDROID_NDK}}"
TOOLCHAIN="$NDK/toolchains/llvm/prebuilt/linux-x86_64"
TARGET="aarch64-linux-android$API"

export CC="$TOOLCHAIN/bin/$TARGET-clang"
export CXX="$TOOLCHAIN/bin/$TARGET-clang++"
export AR="$TOOLCHAIN/bin/llvm-ar"
export LD="$TOOLCHAIN/bin/ld.lld"
export RANLIB="$TOOLCHAIN/bin/llvm-ranlib"
export STRIP="$TOOLCHAIN/bin/llvm-strip"

export SYSROOT="$TOOLCHAIN/sysroot"
export CFLAGS="-fPIC -fPIE -O2 -DANDROID"
export LDFLAGS="-pie"

# Directories
BUILD_ROOT="${BUILD_ROOT:-$(pwd)/build-root}"
STAGE_DIR="$BUILD_ROOT/stage/$PKG_NAME"
FILES_DIR="$STAGE_DIR/files"

# Download, build, install
# ... your build commands ...

# Generate package metadata
cd "$STAGE_DIR"
find files -type f -exec sha256sum {} \; > checksums

# Create CONTROL and manifest.json
# ...

# Package
tar -cJf "$BUILD_ROOT/out/${PKG_NAME}-${VERSION}-${RELEASE}.${ARCH}.txpkg" \
  CONTROL manifest.json checksums files/
```

## Adding New Packages

### Step 1: Find the Termux Package

Search the Termux repository:

```bash
curl -s "https://packages.termux.dev/apt/termux-main/dists/stable/main/binary-aarch64/Packages" | \
  grep -A 5 "^Package: <name>$"
```

### Step 2: Add Package Definition

Add to `build/packages.py`:

```python
"my-package": {
    "termux_name": "my-package",
    "version": "1.0.0",
    "release": 0,
    "desc": "Short description",
    "license": "MIT",
    "cat": "utils",
    "deps": "ndk-sysroot zlib",
    "prov": "",
    "prio": 2,
    "homepage": "https://example.com",
},
```

### Step 3: Determine Priority

Set priority based on dependencies:
- Priority 0: No TX package dependencies
- Priority 1+: Depends on packages with lower priority

### Step 4: Build and Test

```bash
./build.sh pkg my-package
./build.sh validate
```

### Step 5: Update Repository Metadata

```bash
./build.sh metadata
```

## Troubleshooting

### Build Failures

**Problem**: `Package not found in Termux repository`

```
ERROR: Termux package 'my-package' not found
```

**Solution**: Check the exact Termux package name:
```bash
curl -s "https://packages.termux.dev/apt/termux-main/dists/stable/main/binary-aarch64/Packages" | \
  grep "^Package: " | grep -i "my-package"
```

---

**Problem**: `Invalid ELF binary - wrong architecture`

**Solution**: Ensure the Termux package is for aarch64, not x86_64.

---

**Problem**: `Download timeout`

**Solution**: Check network connectivity or use a mirror:
```bash
# In build/packages.py, update:
TERMUX_REPO_URL = "https://mirrors.tuna.tsinghua.edu.cn/termux/apt/termux-main"
```

---

**Problem**: `NDK not found`

```
ERROR: ANDROID_NDK not set or invalid
```

**Solution**:
```bash
export ANDROID_NDK=/path/to/your/ndk
./build.sh ndk-setup
```

---

**Problem**: `readelf/objdump not found`

**Solution**: Install binutils:
```bash
# Debian/Ubuntu
sudo apt-get install binutils

# Fedora
sudo dnf install binutils

# Arch
sudo pacman -S binutils
```

---

**Problem**: `Permission denied on build scripts`

**Solution**:
```bash
chmod +x build.sh build/ndk-scripts/*.sh
```

---

### Validation Failures

**Problem**: Binary uses musl interpreter

```
[FAIL] package.txpkg
       ERROR: [usr/bin/program] Uses musl libc interpreter
```

**Solution**: This package was built against musl, not Bionic. Use Termux repackage mode or rebuild with NDK targeting Bionic.

---

**Problem**: Not a PIE executable

```
[FAIL] package.txpkg
       ERROR: [usr/bin/program] Not a PIE executable or shared library
```

**Solution**: Add `-fPIE -pie` to CFLAGS/LDFLAGS when building from source.

---

### Common NDK Build Issues

**Problem**: `configure: error: C compiler cannot create executables`

**Solution**: Verify your NDK toolchain:
```bash
$CC --version
$CC -v 2>&1 | head -20
```

---

**Problem**: Missing headers (`stdio.h` not found)

**Solution**: Set sysroot correctly:
```bash
export CFLAGS="--sysroot=$SYSROOT $CFLAGS"
```

---

**Problem**: Link errors about undefined symbols

**Solution**: Link against Bionic libraries explicitly:
```bash
export LDFLAGS="-L$SYSROOT/usr/lib/aarch64-linux-android/$API $LDFLAGS"
```

---

## Advanced Topics

### Cross-Compilation with Custom Toolchains

For packages requiring custom toolchains:

```bash
# Custom toolchain path
export CUSTOM_TOOLCHAIN=/opt/custom-toolchain
export CC="$CUSTOM_TOOLCHAIN/bin/clang"
export CXX="$CUSTOM_TOOLCHAIN/bin/clang++"
# ... etc
```

### Static vs Dynamic Linking

**Dynamic linking** (preferred for libraries):
- Smaller binaries
- Shared memory for libraries
- Easier updates

**Static linking** (for special cases):
- No runtime dependencies
- Larger binaries
- Used for some Termux packages

### Stripping Binaries

Always strip debug symbols before packaging:

```bash
$STRIP --strip-debug <binary>        # Keep symbols for backtraces
$STRIP --strip-unneeded <library>    # For shared libraries
$STRIP --strip-all <binary>          # Maximum stripping
```

### Optimizations

| Flag | Description | When to Use |
|------|-------------|-------------|
| `-O2` | Standard optimization | Default |
| `-O3` | Aggressive optimization | When speed matters |
| `-Os` | Size optimization | When binary size matters |
| `-Oz` | Aggressive size optimization | Minimal size |
| `-flto` | Link-time optimization | Maximum optimization |

## Resources

- [Android NDK Guide](https://developer.android.com/ndk/guides)
- [Termux Packages Repository](https://github.com/termux/termux-packages)
- [TX Terminal](https://github.com/Rick000000007/TX-Terminal-Emu)
- [TX-PKG](https://github.com/Rick000000007/tx-pkg)
