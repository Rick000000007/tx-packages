# TX Bionic Package Repository

Complete Android Bionic libc package ecosystem for TX Terminal.

## Overview

This repository provides the permanent package ecosystem for TX Terminal, rebuilt from the ground up to use **Android Bionic libc** instead of musl. All packages are native Android ARM64 (aarch64) binaries that execute directly inside TX Terminal without emulation, compatibility layers, or missing interpreter errors.

## Key Changes from Previous Repository

| Aspect | Old (v1) | New (v2 Bionic) |
|--------|----------|-----------------|
| libc | musl | Android Bionic |
| Interpreter | `/lib/ld-musl-aarch64.so.1` | `/system/bin/linker64` |
| Source | Alpine Linux APKs | Termux packages + NDK builds |
| Target | Generic Linux ARM64 | Native Android ARM64 |
| Compatibility | Requires musl loader | Native Android execution |

## Repository Statistics

- **54+ packages** across all categories
- **100% Android Bionic** - every binary verified
- **API Level 29+** compatible
- **PIE executables** throughout
- **SHA-256 verification** for all packages

## Package Categories

### Core Utilities
| Package | Description |
|---------|-------------|
| `coreutils` | GNU core utilities (file, shell, text tools) |
| `findutils` | GNU file finding utilities |
| `diffutils` | GNU diff utilities |
| `grep` | GNU pattern matching |
| `sed` | GNU stream editor |
| `gawk` | GNU awk text processing |
| `which` | Program locator |
| `file` | File type identification |
| `less` | Terminal pager |

### Editors
| Package | Description |
|---------|-------------|
| `nano` | Lightweight terminal text editor |

### Compression
| Package | Description |
|---------|-------------|
| `gzip` | GNU gzip compression |
| `bzip2` | Bzip2 compression |
| `xz` | XZ and LZMA compression |
| `zstd` | Zstandard compression |
| `lz4` | LZ4 compression |
| `tar` | GNU tar archiver |
| `zip` | Info-ZIP compression |
| `unzip` | Info-ZIP decompression |

### Networking
| Package | Description |
|---------|-------------|
| `curl` | URL data transfer tool |
| `wget` | Web file retrieval |
| `openssh-client` | SSH client (ssh, scp, sftp) |
| `openssl` | TLS/SSL toolkit |
| `ca-certificates` | CA certificates for SSL/TLS |

### Development
| Package | Description |
|---------|-------------|
| `make` | GNU make build automation |
| `patch` | GNU patch utility |
| `pkgconf` | Package compiler/linker metadata |
| `git` | Distributed version control |

### Libraries
All required libraries including: `zlib`, `liblzma`, `libzstd`, `libbz2`, `libffi`, `libedit`, `readline`, `ncurses`, `pcre2`, `openssl`, `libssh2`, `nghttp2`, `brotli`, `gmp`, `mpfr4`, `libunistring`, `libidn2`, and more.

## Target Platform

- **OS**: Android
- **Architecture**: arm64-v8a (AArch64)
- **API Level**: 29+ (Android 10+)
- **API Level 34**: Compatible (Android 14)
- **libc**: Android Bionic
- **Executables**: PIE (Position Independent)
- **Dynamic Linker**: `/system/bin/linker64`

## What Was Removed

The following packages from the musl-based repository are no longer needed or have been replaced:

| Removed Package | Reason |
|-----------------|--------|
| `musl` | Android provides Bionic libc |
| `libgcc` | Replaced by `libcompiler-rt` |
| `libstdc++` | Android NDK provides `libc++` |
| `libandroid-support` | Now included as proper dependency |

## Quick Start

### Using TX-PKG

```bash
# Update package lists
pkg update

# Search for packages
pkg search <query>

# Install a package
pkg install nano curl git

# Show package info
pkg info nano

# List installed packages
pkg list

# Remove a package
pkg remove nano

# Upgrade all packages
pkg upgrade
```

### Repository Configuration

Add to `~/.tx/etc/txpkg/repositories.conf`:

```json
{
  "repositories": [
    {
      "name": "tx-bionic",
      "url": "https://rick000000007.github.io/tx-packages",
      "channel": "stable",
      "priority": 100,
      "enabled": true
    }
  ]
}
```

## Building Packages

### Prerequisites

- Python 3.8+
- Linux x86_64 build host
- Network access to Termux package mirrors
- Android NDK (for source builds)

### Build All Packages

```bash
./build.sh all
```

### Build Single Package

```bash
./build.sh pkg curl
```

### Validate Repository

```bash
./build.sh validate
```

### NDK Setup Check

```bash
export ANDROID_NDK=/path/to/android-ndk
./build.sh ndk-setup
```

## Build System Architecture

```
tx-bionic/
|
├── build.sh                    # Main build entry point
├── build/
│   ├── build_system.py         # Core build system
│   ├── packages.py             # Package definitions & mappings
│   ├── validate_repo.py        # Repository validator
│   ├── ndk_template.sh         # NDK environment template
│   └── ndk-scripts/            # Per-package NDK build scripts
│       ├── 01_zlib.sh
│       ├── 02_openssl.sh
│       └── ...
├── repo/
│   └── stable/
│       ├── Packages.json       # Package catalog
│       ├── index.json          # Repository metadata
│       ├── SHA256SUMS          # Package checksums
│       └── packages/           # .txpkg package archives
└── docs/                       # Documentation
```

## How It Works

1. **Download**: Fetches Android Bionic binaries from Termux repository
2. **Extract**: Decompresses the .deb package
3. **Transform**: Maps Termux paths to TX package layout (`files/usr/`)
4. **Metadata**: Updates CONTROL and manifest.json (removes musl deps)
5. **Validate**: Verifies AArch64, PIE, Bionic-only linkage
6. **Package**: Creates .txpkg (tar.xz) with CONTROL, manifest.json, checksums, files/

## Binary Validation

Every binary is validated for:

- **Architecture**: Must be `AArch64` (ARM64)
- **PIE**: Position Independent Executable
- **Interpreter**: Must use Android Bionic linker (`linker64`), NEVER musl or glibc
- **Dependencies**: Must only link Bionic libraries, never musl (`ld-musl-`) or glibc (`ld-linux-`)

Validation commands used:

```bash
file <binary>
readelf -h <binary>
readelf -l <binary>
readelf -d <binary>
objdump -p <binary>
```

## TX Terminal Integration

TX Terminal provides:
- Meefik's `libbusybox.so`
- `/bin/sh` via BusyBox
- All BusyBox applets

Packages in this repository:
- Install into the TX Runtime prefix
- Assume BusyBox is present
- Do not include BusyBox or any shell
- Are native Android Bionic ARM64

## NDK Source Builds

For packages not available in Termux or requiring custom patches, use the provided NDK build scripts:

```bash
export ANDROID_NDK=/opt/android-ndk
export API=29
cd build/ndk-scripts
./01_zlib.sh
```

See `docs/BUILD_GUIDE.md` for detailed instructions on building from source with the Android NDK.

## Contributing

1. Fork the repository
2. Add package definitions in `build/packages.py`
3. Add NDK build script if needed (for custom builds)
4. Run `./build.sh validate`
5. Create a pull request

## Documentation

| Document | Description |
|----------|-------------|
| [BUILD_GUIDE.md](docs/BUILD_GUIDE.md) | Building packages from source with NDK |
| [NDK_SETUP.md](docs/NDK_SETUP.md) | Android NDK installation and configuration |
| [VALIDATION.md](docs/VALIDATION.md) | Package validation procedures |
| [PACKAGE_FORMAT.md](docs/PACKAGE_FORMAT.md) | .txpkg format specification |

## License

This build system and repository infrastructure are licensed under the MIT License. Individual packages retain their original licenses as specified in their `CONTROL` and `manifest.json` files.

## Acknowledgments

- **Termux** for providing pre-built Android Bionic packages
- **TX Terminal** project for the Android terminal environment
- **Android NDK** team for the native development kit
- The open-source community for all the packaged software
