#!/bin/bash
# ============================================================================
# NDK Build Script: zlib
# Dependencies: none (ndk-sysroot)
# ============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../ndk_template.sh" 2>/dev/null || true

PKG_NAME="zlib"
VERSION="1.3.1"
RELEASE="0"
ARCH="aarch64"
API="${API:-29}"

# Source
SRC_URL="https://github.com/madler/zlib/releases/download/v${VERSION}/zlib-${VERSION}.tar.gz"
SRC_DIR="zlib-${VERSION}"

# Directories
BUILD_ROOT="${BUILD_ROOT:-$(pwd)/build-root}"
SRC_ROOT="$BUILD_ROOT/src"
STAGE_DIR="$BUILD_ROOT/stage/$PKG_NAME"
FILES_DIR="$STAGE_DIR/files"

echo "========================================"
echo "Building $PKG_NAME $VERSION-$RELEASE"
echo "========================================"

# Download and extract
mkdir -p "$SRC_ROOT"
cd "$SRC_ROOT"

if [ ! -d "$SRC_DIR" ]; then
    echo "Downloading source..."
    curl -L -o "${SRC_DIR}.tar.gz" "$SRC_URL"
    tar -xzf "${SRC_DIR}.tar.gz"
fi

cd "$SRC_DIR"

# Clean staging
rm -rf "$STAGE_DIR"
mkdir -p "$FILES_DIR/usr/lib" "$FILES_DIR/usr/include"

# Configure and build
echo "Configuring..."
export CHOST="$TARGET"
./configure \
    --prefix=/usr \
    --libdir=/usr/lib \
    --sharedlibdir=/usr/lib \
    --const

echo "Building..."
make -j$(nproc)

echo "Installing to staging..."
make DESTDIR="$FILES_DIR" install

# Clean up
rm -f "$FILES_DIR/usr/lib"/*.la

# Strip binaries
find "$FILES_DIR" -name "*.so*" -exec $STRIP --strip-unneeded {} \; 2>/dev/null || true

# Generate metadata
echo "Generating package metadata..."
cd "$STAGE_DIR"

# checksums
find files -type f -exec sha256sum {} \; > checksums

# CONTROL
cat > CONTROL <<EOF
Package: $PKG_NAME
Version: $VERSION
Release: $RELEASE
Architecture: $ARCH
License: Zlib
Description: Deflate compression library
Homepage: https://www.zlib.net/
Maintainer: TX Packages <packages@txterminal.dev>
Category: libraries
Essential: no
Depends: ndk-sysroot
Provides: 
Conflicts:
Replaces:
Breaks:
Suggests:
Recommends:
Optional:
EOF

# manifest.json
INSTALLED_SIZE=$(du -sb files | cut -f1)
cat > manifest.json <<EOF
{
  "name": "$PKG_NAME",
  "version": "$VERSION",
  "release": $RELEASE,
  "architecture": "$ARCH",
  "license": "Zlib",
  "description": "Deflate compression library",
  "homepage": "https://www.zlib.net/",
  "maintainer": "TX Packages <packages@txterminal.dev>",
  "category": "libraries",
  "essential": false,
  "depends": "ndk-sysroot",
  "provides": "",
  "conflicts": "",
  "sha256": "",
  "size": 0,
  "installed_size": $INSTALLED_SIZE,
  "format_version": 2,
  "metadata_version": 2,
  "built_for": "android-bionic"
}
EOF

# Create .txpkg
TXPKG_NAME="${PKG_NAME}-${VERSION}-${RELEASE}.${ARCH}.txpkg"
mkdir -p "$BUILD_ROOT/out"
tar -cJf "$BUILD_ROOT/out/$TXPKG_NAME" CONTROL manifest.json checksums files/

echo ""
echo "SUCCESS: Built $TXPKG_NAME"
echo "Output: $BUILD_ROOT/out/$TXPKG_NAME"
echo ""

# Validate binary
echo "Validating binary..."
file "$FILES_DIR/usr/lib/libz.so"
readelf -h "$FILES_DIR/usr/lib/libz.so" | head -5
readelf -d "$FILES_DIR/usr/lib/libz.so" | grep NEEDED
