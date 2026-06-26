# TX Package Format Specification v2.1 (Bionic)

## Overview

TX Packages use the `.txpkg` file extension and follow a `tar.xz` archive format containing package metadata, installation scripts, and payload files. This specification defines version 2.1, updated for the Bionic-based repository.

## Changes from v2.0

| Aspect | v2.0 (musl) | v2.1 (Bionic) |
|--------|-------------|---------------|
| `built_for` field | Not present | `"android-bionic"` |
| `api_level` field | Not present | `"29+"` |
| Dependencies | Include `musl` | `musl` removed, use `ndk-sysroot` |
| Interpreter | `/lib/ld-musl-aarch64.so.1` | `/system/bin/linker64` |

## File Naming

```
<name>-<version>-<release>.<architecture>.txpkg
```

Example: `curl-8.11.1-0.aarch64.txpkg`

## Archive Structure

```
package.txpkg (tar.xz)
|-- CONTROL           # Debian-style control file (required)
|-- manifest.json     # JSON metadata (required)
|-- checksums         # SHA-256 checksums of payload files (required)
|-- preinst           # Pre-installation script (optional)
|-- postinst          # Post-installation script (optional)
|-- prerm             # Pre-removal script (optional)
|-- postrm            # Post-removal script (optional)
`-- files/            # Package payload files (required)
    `-- usr/          # Unified prefix (required)
        |-- bin/      # Executable programs
        |-- lib/      # Shared libraries
        |-- share/    # Architecture-independent data
        `-- include/  # C header files
```

## Unified Layout Requirement

All packages MUST use the `files/usr/` layout. Do NOT mix layouts.

### Correct Layout

```
files/
`-- usr/
    |-- bin/
    |   |-- curl
    |   `-- curl-config
    |-- lib/
    |   |-- libcurl.so
    |   `-- libcurl.so.4
    |-- share/
    |   |-- man/
    |   `-- doc/
    `-- include/
        `-- curl/
```

### Incorrect Layouts

```
# WRONG: No usr prefix
files/
|-- bin/
`-- lib/

# WRONG: Mixed layouts
files/
|-- bin/
`-- usr/
    `-- lib/

# WRONG: Termux prefix
files/
`-- data/
    `-- data/
        `-- com.termux/
            `-- files/
                `-- usr/
```

## CONTROL File

```
Package: curl
Version: 8.11.1
Release: 0
Architecture: aarch64
License: curl
Description: Command-line tool for transferring data with URLs
Homepage: https://curl.se/
Maintainer: TX Packages <packages@txterminal.dev>
Category: network
Essential: no
Depends: ndk-sysroot openssl zlib libssh2 nghttp2-libs zstd
Provides: 
Conflicts:
Replaces:
Breaks:
Suggests:
Recommends:
Optional:
```

### Required Fields

| Field | Description |
|-------|-------------|
| `Package` | Package name (max 128 chars) |
| `Version` | Upstream version string |
| `Release` | Package release number |
| `Architecture` | Target architecture (`aarch64`) |

### Optional Fields

| Field | Description |
|-------|-------------|
| `License` | Software license identifier (SPDX) |
| `Description` | Short package description |
| `Homepage` | Project homepage URL |
| `Maintainer` | Package maintainer contact |
| `Category` | Package category |
| `Essential` | `yes` marks package as essential |
| `Depends` | Space-separated dependency list |
| `Provides` | Virtual packages provided |
| `Conflicts` | Conflicting packages |
| `Replaces` | Packages this replaces |
| `Breaks` | Packages broken by this |
| `Suggests` | Suggested packages |
| `Recommends` | Recommended packages |
| `Optional` | Optional dependencies |

## manifest.json

```json
{
  "name": "curl",
  "version": "8.11.1",
  "release": 0,
  "architecture": "aarch64",
  "license": "curl",
  "description": "Command-line tool for transferring data with URLs",
  "homepage": "https://curl.se/",
  "maintainer": "TX Packages <packages@txterminal.dev>",
  "category": "network",
  "essential": false,
  "depends": "ndk-sysroot openssl zlib libssh2 nghttp2-libs zstd",
  "provides": "",
  "conflicts": "",
  "sha256": "abc123...",
  "size": 150000,
  "installed_size": 450000,
  "format_version": 2,
  "metadata_version": 2,
  "built_for": "android-bionic",
  "api_level": "29+"
}
```

### New Fields in v2.1

| Field | Value | Description |
|-------|-------|-------------|
| `built_for` | `"android-bionic"` | Indicates Bionic-based build |
| `api_level` | `"29+"` | Minimum Android API level |

## checksums

```
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  usr/bin/curl
a3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b856  usr/lib/libcurl.so
```

Format: `<sha256>  <relative_path>` (relative to `files/`)

## Installation Scripts

All scripts are optional. When present, they must be executable (mode 0755).

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PREFIX` | Installation prefix |
| `PKG_NAME` | Package name |
| `PKG_VERSION` | Package version |
| `PKG_RELEASE` | Package release |

### preinst

```sh
#!/bin/sh
echo "Preparing to install $PKG_NAME..."
```

### postinst

```sh
#!/bin/sh
echo "$PKG_NAME installed successfully."
```

## Architecture

All packages must target `aarch64` (Android arm64-v8a). Binaries must:

- Be compiled for Android AArch64
- Use PIE (Position Independent Executable) format
- Use Android's Bionic linker (`/system/bin/linker64`)
- Support API level 29+
- Never reference musl or glibc

## Compatibility

TX Terminal provides:
- Meefik's `libbusybox.so`
- `/bin/sh` (BusyBox)
- All BusyBox applets

Packages must:
- Assume BusyBox is present
- Not include BusyBox or any shell
- Install into `files/usr/` prefix
- Be native Android Bionic ARM64

## Version History

| Version | Changes |
|---------|---------|
| 1.0 | Initial format |
| 2.0 | Added manifest.json, format_version, metadata_version |
| 2.1 | Added `built_for` and `api_level` fields for Bionic builds |
