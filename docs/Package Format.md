# TX Package Format Specification

## Overview

TX Packages use the `.txpkg` file extension and follow a tar.xz archive format containing package metadata, installation scripts, and payload files. This specification defines version 2.0 of the TX Package format, compatible with TX-PKG v1.0+.

## File Naming

```
<name>-<version>-<release>.<architecture>.txpkg
```

Example: `nano-7.2-1.aarch64.txpkg`

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
    |-- usr/
    |   |-- bin/      # Executables
    |   |-- lib/      # Libraries
    |   |-- share/    # Shared data files
    |   `-- include/  # Header files
    `-- etc/          # Configuration files
```

## CONTROL File

The CONTROL file is a Debian-style control file with key-value pairs:

```
Package: nano
Version: 7.2
Release: 1
Architecture: aarch64
License: GPL-3.0+
Description: Lightweight terminal text editor
Homepage: https://www.nano-editor.org/
Maintainer: TX Packages <packages@txterminal.dev>
Category: editors
Essential: no
Depends: musl ncurses-libs ncurses-terminfo
Provides: editor
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
| `Depends` | Comma-separated dependency list |
| `Provides` | Virtual packages provided |
| `Conflicts` | Conflicting packages |
| `Replaces` | Packages this replaces |
| `Breaks` | Packages broken by this |
| `Suggests` | Suggested packages |
| `Recommends` | Recommended packages |
| `Optional` | Optional dependencies |

## manifest.json

JSON representation of the same CONTROL metadata:

```json
{
  "name": "nano",
  "version": "7.2",
  "release": 1,
  "architecture": "aarch64",
  "license": "GPL-3.0+",
  "description": "Lightweight terminal text editor",
  "homepage": "https://www.nano-editor.org/",
  "maintainer": "TX Packages <packages@txterminal.dev>",
  "category": "editors",
  "essential": false,
  "depends": "musl ncurses-libs ncurses-terminfo",
  "provides": "editor",
  "conflicts": "",
  "sha256": "abc123...",
  "size": 122604,
  "installed_size": 380000
}
```

## checksums

SHA-256 checksums of all payload files in `files/`:

```
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  usr/bin/nano
a3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b856  usr/share/doc/nano/README
```

Format: `<sha256>  <relative_path>`

## Installation Scripts

All scripts are optional. When present, they must be executable (mode 0755).

### Environment Variables

The following environment variables are available to all scripts:

| Variable | Description |
|----------|-------------|
| `PREFIX` | Installation prefix (e.g., `/data/data/dev.termux/files/usr`) |
| `PKG_NAME` | Package name |
| `PKG_VERSION` | Package version |
| `PKG_RELEASE` | Package release |

### preinst

Runs before package extraction:

```sh
#!/bin/sh
echo "Preparing to install $PKG_NAME..."
```

### postinst

Runs after file installation:

```sh
#!/bin/sh
# Update icon cache, register services, etc.
echo "$PKG_NAME installed successfully."
```

### prerm

Runs before package removal:

```sh
#!/bin/sh
# Stop services, unregister, etc.
```

### postrm

Runs after package removal:

```sh
#!/bin/sh
# Clean up remaining files
```

## Payload Files (files/)

All payload files are installed relative to the TX Runtime prefix. The standard layout is:

```
files/
`-- usr/
    |-- bin/        # Executable programs
    |-- lib/        # Shared libraries
    |-- share/      # Architecture-independent data
    |   `-- doc/    # Documentation
    `-- include/    # C header files
```

Packages must not include:
- BusyBox or any shell implementation
- Files in `/system` or hardcoded `/usr` paths
- Desktop Linux-specific files
- Root-only assumptions

## Architecture

All packages must target `aarch64` (Android arm64-v8a). Binaries must:

- Be compiled for Android AArch64
- Use PIE (Position Independent Executable) format
- Support modern Android security requirements
- Use musl libc (for Alpine-based packages)
- Avoid glibc dependencies
- Avoid desktop Linux assumptions

## Compatibility

TX Terminal permanently provides:
- Meefik's `libbusybox.so`
- `/bin/sh` (BusyBox)
- All BusyBox applets

Packages must assume BusyBox is present and must not include duplicate utilities.

## Version History

| Version | Changes |
|---------|---------|
| 1.0 | Initial format |
| 2.0 | Added manifest.json, format_version, metadata_version |
