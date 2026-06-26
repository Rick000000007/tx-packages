# TX Package Creation Guide

## Overview

This guide explains how to create TX Packages manually, from scratch. This is useful for packages not available in Alpine Linux or for custom software.

## Prerequisites

- TX Package Manager installed
- Basic knowledge of shell scripting
- Android cross-compilation toolchain (for native binaries)

## Creating a Package Step by Step

### Step 1: Create the Directory Structure

```bash
mkdir -p mypkg/files/usr/bin
mkdir -p mypkg/files/usr/share/doc/mypkg
```

### Step 2: Add Your Binaries

Place compiled binaries in the appropriate directories:

```bash
cp my-program mypkg/files/usr/bin/
cp README LICENSE mypkg/files/usr/share/doc/mypkg/
```

**Important**: Binaries must be:
- Compiled for Android arm64-v8a (AArch64)
- PIE (Position Independent Executable)
- Linked against musl libc (preferred) or Bionic

### Step 3: Create the CONTROL File

```bash
cat > mypkg/CONTROL <<'EOF'
Package: mypkg
Version: 1.0.0
Release: 1
Architecture: aarch64
License: MIT
Description: My first TX package
 This is a longer description that can span
 multiple lines with indentation.
Homepage: https://example.com/mypkg
Maintainer: Your Name <you@example.com>
Category: utils
Essential: no
Depends: musl
Provides:
Conflicts:
Replaces:
Breaks:
Suggests:
Recommends:
Optional:
EOF
```

### Step 4: Create manifest.json

```bash
cat > mypkg/manifest.json <<'EOF'
{
  "name": "mypkg",
  "version": "1.0.0",
  "release": 1,
  "architecture": "aarch64",
  "license": "MIT",
  "description": "My first TX package",
  "homepage": "https://example.com/mypkg",
  "maintainer": "Your Name <you@example.com>",
  "category": "utils",
  "essential": false,
  "depends": "musl",
  "provides": "",
  "conflicts": "",
  "sha256": "",
  "size": 0,
  "installed_size": 0
}
EOF
```

### Step 5: Create the Checksums File

```bash
cd mypkg/files
find . -type f -exec sha256sum {} \; > ../checksums
cd ../..
```

The checksums file format:
```
<sha256hash>  <relative_path>
```

Example:
```
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  usr/bin/my-program
```

### Step 6: Add Installation Scripts (Optional)

```bash
cat > mypkg/postinst <<'EOF'
#!/bin/sh
echo "$PKG_NAME $PKG_VERSION installed successfully."
EOF
chmod 755 mypkg/postinst
```

Available scripts:
- `preinst` - Runs before package extraction
- `postinst` - Runs after file installation
- `prerm` - Runs before package removal
- `postrm` - Runs after package removal

### Step 7: Create the .txpkg Archive

```bash
cd mypkg
tar -cJf mypkg-1.0.0-1.aarch64.txpkg \
  CONTROL manifest.json checksums \
  preinst postinst prerm postrm \
  files/
```

### Step 8: Compute the SHA-256 Hash

```bash
sha256sum mypkg-1.0.0-1.aarch64.txpkg
```

Update `manifest.json` with the computed hash and file size.

### Step 9: Validate the Package

```bash
# List contents
tar -tf mypkg-1.0.0-1.aarch64.txpkg

# Verify structure
tar -xf mypkg-1.0.0-1.aarch64.txpkg -O manifest.json | python3 -m json.tool
```

## Package Categories

Use one of the following categories:

| Category | Description |
|----------|-------------|
| `system` | System utilities and core tools |
| `libraries` | Shared libraries and development libraries |
| `development` | Compilers, build tools, development utilities |
| `network` | Networking tools and clients |
| `compression` | Compression and archiving tools |
| `editors` | Text editors and IDEs |
| `security` | Security tools and certificates |
| `utils` | General utilities |
| `misc` | Miscellaneous packages |

## Dependency Declaration

### Simple Dependencies

```
Depends: musl
```

### Multiple Dependencies

```
Depends: musl zlib openssl
```

### Version Constraints (Not Yet Supported)

Future versions may support:

```
Depends: musl (>= 1.2.0), zlib (>= 1.2.0)
```

For now, use plain package names:

```
Depends: musl zlib
```

### Virtual Packages

Declare what virtual packages your package provides:

```
Provides: editor
```

Other packages can then depend on the virtual package:

```
Depends: editor
```

This allows any package providing `editor` to satisfy the dependency.

## Cross-Compiling for Android

### Using Android NDK

```bash
# Set up the toolchain
export NDK=/path/to/android-ndk
export TOOLCHAIN=$NDK/toolchains/llvm/prebuilt/linux-x86_64
export TARGET=aarch64-linux-android29
export CC=$TOOLCHAIN/bin/$TARGET-clang
export CXX=$TOOLCHAIN/bin/$TARGET-clang++

# Compile
$CC -o myprogram -fPIE -pie myprogram.c
```

### Using musl-cross-make

```bash
# Install musl-cross-make
# https://github.com/richfelker/musl-cross-make

export CC=aarch64-linux-musl-gcc
export CFLAGS="-fPIE -pie"

$CC $CFLAGS -o myprogram myprogram.c
```

### Static Linking

For maximum compatibility, statically link against musl:

```bash
$CC -static -o myprogram myprogram.c
```

## Testing Your Package

### Manual Test

```bash
# Copy to TX Terminal
cp mypkg-1.0.0-1.aarch64.txpkg /sdcard/Download/

# In TX Terminal
pkg install /sdcard/Download/mypkg-1.0.0-1.aarch64.txkg
which myprogram
myprogram --version
pkg remove mypkg
```

### Automated Test Script

```bash
#!/bin/bash
set -e

PKG="mypkg-1.0.0-1.aarch64.txpkg"

echo "Installing..."
pkg install "$PKG"

echo "Verifying installation..."
test -f "$PREFIX/usr/bin/myprogram"

echo "Testing execution..."
myprogram --version

echo "Removing..."
pkg remove mypkg

echo "All tests passed!"
```

## Common Issues

### "Bad ELF interpreter"

The binary was compiled for the wrong architecture. Ensure:
- Use `aarch64-linux-android` target
- Check with `file myprogram` - should show `ELF 64-bit LSB executable, ARM aarch64`

### "PIE executable required"

Android requires PIE executables. Compile with:
```bash
$CC -fPIE -pie -o myprogram myprogram.c
```

### Missing Libraries

If your binary needs shared libraries:
- Package the libraries alongside your binary
- Or statically link your binary
- List library dependencies in the `Depends` field

### "Permission denied"

Ensure binaries are executable:
```bash
chmod 755 mypkg/files/usr/bin/myprogram
```

## Tips

### Keep Packages Small

- Strip debug symbols: `strip myprogram`
- Use UPX for compression (optional)
- Remove unnecessary files

### Use Proper File Permissions

```
755 for executables and directories
644 for data files and libraries
```

### Include Documentation

Always include at minimum:
- README or description
- License file
- Basic usage information

### Follow Naming Conventions

- Package names: lowercase, alphanumeric, hyphens allowed
- Version numbers: semantic versioning preferred
- Release numbers: integer starting from 1

## Example: Complete Package

See the `build/` directory in this repository for real-world examples of how packages are built from Alpine Linux sources.

For a minimal example:

```
mypkg/
├── CONTROL
├── manifest.json
├── checksums
├── postinst
└── files/
    └── usr/
        ├── bin/
        │   └── myprogram
        └── share/
            └── doc/
                └── mypkg/
                    ├── README
                    └── LICENSE
```

## Submitting Packages

To submit a package to the official repository:

1. Fork the tx-packages repository
2. Add your package definition to `build/build_final.py`
3. Build and validate
4. Create a pull request with:
   - Package description and justification
   - Dependency analysis
   - Test results

## Resources

- TXPKG Spec: See `docs/Package Format.md`
- Build System: See `docs/Build Guide.md`
- Alpine Packages: https://pkgs.alpinelinux.org/
- Android NDK: https://developer.android.com/ndk
