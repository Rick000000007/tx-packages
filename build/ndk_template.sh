#!/bin/bash
# ============================================================================
# TX Bionic NDK Build Template
# Template for building packages from source with Android NDK
# ============================================================================
# Usage:
#   export NDK=/path/to/android-ndk
#   export API=29
#   ./ndk_template.sh <package_name> <version> <source_url>
# ============================================================================

set -e

# Configuration
: "${NDK:=${ANDROID_NDK}}"
: "${API:=29}"
: "${ARCH:=aarch64}"
: "${HOST_TAG:=linux-x86_64}"

# Validate NDK
if [ -z "$NDK" ] || [ ! -d "$NDK" ]; then
    echo "ERROR: ANDROID_NDK not set or invalid: $NDK"
    echo "Set ANDROID_NDK environment variable to your NDK path"
    exit 1
fi

echo "NDK: $NDK"
echo "API: $API"
echo "ARCH: $ARCH"

# Toolchain setup
TOOLCHAIN="$NDK/toolchains/llvm/prebuilt/$HOST_TAG"
TARGET="aarch64-linux-android$API"

export CC="$TOOLCHAIN/bin/$TARGET-clang"
export CXX="$TOOLCHAIN/bin/$TARGET-clang++"
export AR="$TOOLCHAIN/bin/llvm-ar"
export AS="$CC"
export LD="$TOOLCHAIN/bin/ld.lld"
export RANLIB="$TOOLCHAIN/bin/llvm-ranlib"
export STRIP="$TOOLCHAIN/bin/llvm-strip"
export NM="$TOOLCHAIN/bin/llvm-nm"
export OBJDUMP="$TOOLCHAIN/bin/llvm-objdump"
export READELF="$TOOLCHAIN/bin/llvm-readelf"

# Sysroot
export SYSROOT="$TOOLCHAIN/sysroot"
export CFLAGS="-fPIC -fPIE -O2 -DANDROID -I$SYSROOT/usr/include"
export CXXFLAGS="$CFLAGS"
export LDFLAGS="-pie -L$SYSROOT/usr/lib/aarch64-linux-android/$API"

# Verify toolchain exists
for tool in CC CXX AR LD RANLIB STRIP; do
    tool_path="${!tool}"
    if [ ! -f "$tool_path" ]; then
        echo "ERROR: Tool not found: $tool = $tool_path"
        exit 1
    fi
    echo "  $tool: $tool_path"
done

echo ""
echo "Toolchain verified. Ready to build."
echo ""
echo "Standard build commands:"
echo "  ./configure --host=$TARGET --prefix=/usr --sysroot=$SYSroot"
echo "  make"
echo "  make DESTDIR=\$STAGE_DIR install"
