# TX Packages

Official package collection and build system for TX Terminal.

## Overview

TX Packages provides a complete, production-ready package ecosystem for TX Terminal on Android. All packages are compiled for Android arm64-v8a (AArch64) and distributed in the native `.txpkg` format.

## Features

- **54 Production Packages**: Core utilities, development tools, networking, compression, and libraries
- **Native Android Builds**: All packages compiled for Android arm64-v8a
- **TX-PKG Compatible**: Full compatibility with the TX Package Manager
- **Automated Build System**: Reproducible builds from Alpine Linux sources
- **Dependency Resolution**: Proper dependency graph with no circular dependencies
- **SHA-256 Verification**: Every package cryptographically verified
- **Repository Metadata**: Auto-generated Packages.json, index.json, and SHA256SUMS

## Package Categories

### Development
- `make` - GNU make build automation
- `pkgconf` - Package compiler and linker metadata (provides pkg-config)
- `patch` - GNU patch utility

### Core Utilities
- `coreutils` - GNU core utilities (file, shell, text tools)
- `findutils` - GNU file finding utilities
- `diffutils` - GNU diff utilities
- `grep` - GNU pattern matching
- `sed` - GNU stream editor
- `gawk` - GNU awk
- `nano` - Terminal text editor
- `less` - Terminal pager
- `file` - File type identification
- `which` - Program locator
- `procps` - Process utilities (ps, top, free, pgrep, pkill)
- `psmisc` - Process utilities (fuser, killall, pstree)

### Networking
- `curl` - URL data transfer tool
- `wget` - Web file retrieval
- `openssh-client` - SSH client (ssh, scp, sftp, ssh-keygen)

### Compression
- `gzip` - GNU gzip compression
- `xz` - XZ and LZMA compression
- `bzip2` - Bzip2 compression
- `zip` - Info-ZIP compression
- `unzip` - Info-ZIP decompression
- `tar` - GNU tar archiver
- `zstd` - Zstandard compression
- `lz4` - LZ4 compression

### Libraries
- `musl` - Musl C library (provides libc)
- `openssl` - TLS/SSL toolkit (provides libssl, libcrypto)
- `zlib` - Deflate compression library
- `libarchive` - Multi-format archive library
- `liblzma` - XZ compression library
- `libbz2` - Bzip2 compression library
- `libzstd` - Zstandard compression library
- `pcre2` - Perl-compatible regex library
- `ncurses-libs` - Terminal handling library
- `readline` - Line editing library
- And 20+ more...

### Security
- `ca-certificates` - CA certificates bundle for SSL/TLS
- `ca-certificates-bundle` - Pre-generated CA certificates

## Quick Start

### Using TX-PKG

```bash
# Update package lists
pkg update

# Search for packages
pkg search <query>

# Install a package
pkg install nano

# Show package info
pkg info nano

# List installed packages
pkg list

# Remove a package
pkg remove nano

# Upgrade all packages
pkg upgrade
```

### Adding the Repository

Configure in `~/.tx/etc/txpkg/repositories.conf`:

```json
{
  "repositories": [
    {
      "name": "tx-main",
      "url": "https://rick000000007.github.io/tx-packages",
      "channel": "stable",
      "priority": 100,
      "enabled": true
    }
  ]
}
```

## Repository Structure

```
tx-packages/
|
├── repo/
|   └── stable/
|       ├── Packages.json          # Package catalog
|       ├── index.json             # Repository metadata
|       ├── SHA256SUMS             # Package checksums
|       └── packages/
|           ├── *.txpkg            # Package archives
|           ├── *.json             # Package metadata
|           └── *.sha256           # Package checksums
|
├── build/
|   ├── build_final.py             # Main build script
|   ├── generate-repo-meta.py      # Metadata generator
|   ├── validate-repo.py           # Repository validator
|   └── build.sh                   # Build wrapper
|
├── docs/
|   ├── Package Format.md          # .txpkg specification
|   ├── Repository Guide.md        # Repository maintenance
|   ├── Build Guide.md             # Build system documentation
|   ├── Publishing Guide.md        # Publishing workflow
|   └── Package Creation Guide.md  # Creating custom packages
|
└── README.md                      # This file
```

## Building Packages

### Prerequisites

- Python 3.8+
- Network access to Alpine Linux mirrors

### Build All Packages

```bash
python3 build/build_final.py
```

### Validate Repository

```bash
python3 build/validate-repo.py
```

See `docs/Build Guide.md` for detailed build instructions.

## Creating Custom Packages

See `docs/Package Creation Guide.md` for step-by-step instructions on creating `.txpkg` packages from scratch.

## Documentation

| Document | Description |
|----------|-------------|
| [Package Format](docs/Package%20Format.md) | `.txpkg` file format specification |
| [Repository Guide](docs/Repository%20Guide.md) | Repository structure and maintenance |
| [Build Guide](docs/Build%20Guide.md) | Build system documentation |
| [Publishing Guide](docs/Publishing%20Guide.md) | Publishing workflow |
| [Package Creation Guide](docs/Package%20Creation%20Guide.md) | Creating custom packages |

## Target Platform

- **OS**: Android
- **Architecture**: arm64-v8a (AArch64) only
- **API Level**: 29+
- **Runtime**: TX Terminal
- **Libc**: musl (from Alpine Linux)

## Integration with TX Terminal

TX Terminal provides:
- Meefik's `libbusybox.so`
- `/bin/sh` via BusyBox
- All BusyBox applets

Packages in this repository:
- Install into the TX Runtime prefix
- Assume BusyBox is present
- Do not include BusyBox or any shell
- Are compiled for Android arm64-v8a

## License

This repository and build system are licensed under the MIT License. Individual packages retain their original licenses as specified in their `CONTROL` and `manifest.json` files.

## Contributing

1. Fork the repository
2. Add or update package definitions in `build/build_final.py`
3. Build and validate
4. Create a pull request

See `docs/Package Creation Guide.md` and `docs/Publishing Guide.md` for details.

## Support

- Issues: https://github.com/Rick000000007/tx-packages/issues
- TX Terminal: https://github.com/Rick000000007/TX-Terminal-Emu
- TX-PKG: https://github.com/Rick000000007/tx-pkg

## Acknowledgments

- Alpine Linux for the excellent musl-based distribution
- TX Terminal project for the Android terminal environment
- The open-source community for all the packaged software
