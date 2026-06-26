#!/bin/bash
# ============================================================================
# NDK Build Script: OpenSSL
# Dependencies: ndk-sysroot, ca-certificates-bundle
# ============================================================================
set -e

PKG_NAME="openssl"
VERSION="3.3.2"
RELEASE="0"
ARCH="aarch64"
API="${API:-29}"

: "${NDK:=${ANDROID_NDK}}"
: "${API:=29}"

TOOLCHAIN="$NDK/toolchains/llvm/prebuilt/linux-x86_64"
TARGET="aarch64-linux-android$API"

export CC="$TOOLCHAIN/bin/$TARGET-clang"
export CXX="$TOOLCHAIN/bin/$TARGET-clang++"
export AR="$TOOLCHAIN/bin/llvm-ar"
export AS="$CC"
export LD="$TOOLCHAIN/bin/ld.lld"
export RANLIB="$TOOLCHAIN/bin/llvm-ranlib"
export STRIP="$TOOLCHAIN/bin/llvm-strip"

export SYSROOT="$TOOLCHAIN/sysroot"

# Source
SRC_URL="https://github.com/openssl/openssl/releases/download/openssl-${VERSION}/openssl-${VERSION}.tar.gz"
SRC_DIR="openssl-${VERSION}"

BUILD_ROOT="${BUILD_ROOT:-$(pwd)/build-root}"
SRC_ROOT="$BUILD_ROOT/src"
STAGE_DIR="$BUILD_ROOT/stage/$PKG_NAME"
FILES_DIR="$STAGE_DIR/files"

echo "========================================"
echo "Building $PKG_NAME $VERSION-$RELEASE"
echo "========================================"

mkdir -p "$SRC_ROOT"
cd "$SRC_ROOT"

if [ ! -d "$SRC_DIR" ]; then
    echo "Downloading source..."
    curl -L -o "${SRC_DIR}.tar.gz" "$SRC_URL"
    tar -xzf "${SRC_DIR}.tar.gz"
fi

cd "$SRC_DIR"

rm -rf "$STAGE_DIR"
mkdir -p "$FILES_DIR"

# OpenSSL Android configuration
echo "Configuring OpenSSL for Android..."
./Configure android-arm64 \
    -D__ANDROID_API__=$API \
    --prefix=/usr \
    --openssldir=/etc/ssl \
    --libdir=lib \
    shared \
    no-tests \
    -fPIC -O2

echo "Building..."
make -j$(nproc) build_libs build_apps

echo "Installing to staging..."
make DESTDIR="$FILES_DIR" install_sw

echo "Strip binaries..."
find "$FILES_DIR" -name "*.so*" -exec $STRIP --strip-unneeded {} \; 2>/dev/null || true
find "$FILES_DIR" -type f -executable -exec $STRIP {} \; 2>/dev/null || true

# Generate metadata
echo "Generating package metadata..."
cd "$STAGE_DIR"
find files -type f -exec sha256sum {} \; > checksums

INSTALLED_SIZE=$(du -sb files | cut -f1)

cat > CONTROL <<EOF
Package: $PKG_NAME
Version: $VERSION
Release: $RELEASE
Architecture: $ARCH
License: Apache-2.0
Description: TLS/SSL toolkit
Homepage: https://www.openssl.org/
Maintainer: TX Packages <packages@txterminal.dev>
Category: libraries
Essential: no
Depends: ndk-sysroot ca-certificates-bundle
Provides: libssl libcrypto
Conflicts:
Replaces:
Breaks:
Suggests:
Recommends:
Optional:
EOF

cat > manifest.json <<EOF
{
  "name": "$PKG_NAME",
  "version": "$VERSION",
  "release": $RELEASE,
  "architecture": "$ARCH",
  "license": "Apache-2.0",
  "description": "TLS/SSL toolkit",
  "homepage": "https://www.openssl.org/",
  "maintainer": "TX Packages <packages@txterminal.dev>",
  "category": "libraries",
  "essential": false,
  "depends": "ndk-sysroot ca-certificates-bundle",
  "provides": "libssl libcrypto",
  "conflicts": "",
  "sha256": "",
  "size": 0,
  "installed_size": $INSTALLED_SIZE,
  "format_version": 2,
  "metadata_version": 2,
  "built_for": "android-bionic"
}
EOF

TXPKG_NAME="${PKG_NAME}-${VERSION}-${RELEASE}.${ARCH}.txpkg"
mkdir -p "$BUILD_ROOT/out"
tar -cJf "$BUILD_ROOT/out/$TXPKG_NAME" CONTROL manifest.json checksums files/

echo ""
echo "SUCCESS: Built $TXPKG_NAME"
echo "Output: $BUILD_ROOT/out/$TXPKG_NAME"

# Validation
echo ""
echo "Validation:"
echo "--- libcrypto.so ---"
file "$FILES_DIR/usr/lib/libcrypto.so"
readelf -d "$FILES_DIR/usr/lib/libcrypto.so" | grep -E "NEEDED|SONAME"
echo "--- libssl.so ---"
file "$FILES_DIR/usr/lib/libssl.so"
readelf -d "$FILES_DIR/usr/lib/libssl.so" | grep -E "NEEDED|SONAME"
