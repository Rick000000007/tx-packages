# Android NDK Setup Guide for TX Bionic

Step-by-step guide to installing and configuring the Android NDK for building TX packages.

## Table of Contents

1. [What is the Android NDK?](#what-is-the-android-ndk)
2. [System Requirements](#system-requirements)
3. [Installation Methods](#installation-methods)
4. [Environment Configuration](#environment-configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

## What is the Android NDK?

The Android Native Development Kit (NDK) is a toolset that lets you compile C and C++ code for Android devices. It's required for building packages from source that will run on Android Bionic libc.

### Why We Need the NDK

- Provides the **cross-compilation toolchain** (Clang/LLVM for ARM64)
- Supplies the **Bionic libc headers and libraries**
- Includes the **Android sysroot** with system headers
- Provides **linker and binutils** for ARM64

## System Requirements

- **OS**: Linux x86_64 (Ubuntu 20.04+, Fedora 34+, Debian 11+)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 5GB for NDK + 10GB for builds
- **Internet**: For downloading NDK and sources

## Installation Methods

### Method 1: Direct Download (Recommended)

Download the latest NDK directly from Google:

```bash
# Create installation directory
sudo mkdir -p /opt

# Download NDK r27c (latest stable as of 2024)
cd /tmp
wget https://dl.google.com/android/repository/android-ndk-r27c-linux.zip

# Extract
sudo unzip -q android-ndk-r27c-linux.zip -d /opt/

# Set permissions
sudo chown -R $(whoami):$(whoami) /opt/android-ndk-r27c

# Set environment variable
echo 'export ANDROID_NDK=/opt/android-ndk-r27c' >> ~/.bashrc
source ~/.bashrc
```

### Method 2: Via sdkmanager

If you already have the Android SDK installed:

```bash
# Find your Android SDK
export ANDROID_SDK=$HOME/Android/Sdk

# Use sdkmanager to install NDK
cd $ANDROID_SDK/cmdline-tools/latest/bin
./sdkmanager "ndk;27.0.12077973"

# Set environment variable
echo 'export ANDROID_NDK=$ANDROID_SDK/ndk/27.0.12077973' >> ~/.bashrc
source ~/.bashrc
```

### Method 3: Package Manager (Linux Distributions)

#### Ubuntu/Debian

```bash
# NDK is not available in standard repositories
# Use the direct download method above
```

#### Fedora

```bash
# Install android-tools which may include NDK components
sudo dnf install android-tools

# For full NDK, use direct download method
```

#### Arch Linux

```bash
# Install from AUR
yay -S android-ndk
# or
paru -S android-ndk
```

### Method 4: Docker Container

Use a Docker container with NDK pre-installed:

```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    wget unzip python3 python3-pip \
    build-essential autoconf automake libtool \
    cmake ninja-build pkg-config

# Download and install NDK
RUN wget -q https://dl.google.com/android/repository/android-ndk-r27c-linux.zip -O /tmp/ndk.zip && \
    unzip -q /tmp/ndk.zip -d /opt/ && \
    rm /tmp/ndk.zip

ENV ANDROID_NDK=/opt/android-ndk-r27c
ENV PATH=$ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH

WORKDIR /workspace
```

Build and run:

```bash
docker build -t tx-bionic-build .
docker run -v $(pwd):/workspace -it tx-bionic-build
```

## Environment Configuration

### Required Environment Variables

Add these to your `~/.bashrc`, `~/.zshrc`, or `~/.profile`:

```bash
# Android NDK
export ANDROID_NDK=/opt/android-ndk-r27c
export API_LEVEL=29

# Optional: Add toolchain to PATH
export PATH=$ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH

# Optional: ccache for faster rebuilds
export USE_CCACHE=1
export CCACHE_DIR=$HOME/.ccache
```

### Loading the Configuration

```bash
# Reload shell configuration
source ~/.bashrc

# Or set temporarily for current session
export ANDROID_NDK=/opt/android-ndk-r27c
```

### Understanding the NDK Layout

```
android-ndk-r27c/
├── toolchains/
│   └── llvm/
│       └── prebuilt/
│           └── linux-x86_64/
│               ├── bin/
│               │   ├── aarch64-linux-android29-clang     # C compiler
│               │   ├── aarch64-linux-android29-clang++   # C++ compiler
│               │   ├── ld.lld                           # Linker
│               │   ├── llvm-ar                          # Archiver
│               │   ├── llvm-ranlib                      # Ranlib
│               │   ├── llvm-strip                       # Strip
│               │   └── llvm-readelf                     # Readelf
│               ├── sysroot/
│               │   ├── usr/
│               │   │   ├── include/                     # System headers
│               │   │   │   ├── stdio.h
│               │   │   │   ├── stdlib.h
│               │   │   │   └── ...
│               │   │   └── lib/
│               │   │       └── aarch64-linux-android/
│               │   │           └── 29/
│               │   │               ├── libc.so           # Bionic libc
│               │   │               ├── libm.so
│               │   │               └── ...
│               └── lib/
│                   └── clang/
│                       └── 18.0.3/
│                           └── lib/
│                               └── linux/
│                                   └── libclang_rt.builtins-aarch64-android.a
├── build/
├── meta/
├── prebuilt/
├── sources/
└── CHANGELOG.md
```

## Verification

### Quick Verification

Run the built-in NDK check:

```bash
cd tx-packages
./build.sh ndk-setup
```

Expected output:
```
╔══════════════════════════════════════════════════════════════╗
║           TX Bionic Build System v1.0                        ║
╚══════════════════════════════════════════════════════════════╝

[INFO] NDK: /opt/android-ndk-r27c
[INFO] API: 29
[INFO] ARCH: aarch64
[INFO]   CC: /opt/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android29-clang
[INFO]   CXX: /opt/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android29-clang++
[INFO]   AR: /opt/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-ar
[INFO]   LD: /opt/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/ld.lld
[INFO]   RANLIB: /opt/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-ranlib
[INFO]   STRIP: /opt/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip
[INFO] Toolchain verified. Ready to build.
```

### Manual Verification

#### 1. Check Compiler Version

```bash
$ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android29-clang --version
```

Expected output:
```
Android (12345678, based on r123456) clang version 18.0.3
Target: aarch64-unknown-linux-android29
Thread model: posix
```

#### 2. Verify Sysroot

```bash
ls $ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/include/stdio.h
ls $ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/lib/aarch64-linux-android/29/libc.so
```

Both should exist.

#### 3. Test Compile

```bash
cat > /tmp/test.c << 'EOF'
#include <stdio.h>
int main() {
    printf("Hello Android Bionic!\n");
    return 0;
}
EOF

$ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android29-clang \
    -fPIE -pie -o /tmp/test-android /tmp/test.c

# Verify it's ARM64 PIE
file /tmp/test-android
```

Expected output:
```
/tmp/test-android: ELF 64-bit LSB pie executable, ARM aarch64, version 1 (SYSV), dynamically linked, interpreter /system/bin/linker64, BuildID[sha1]=..., stripped
```

Key things to verify:
- `ARM aarch64` - correct architecture
- `pie executable` - PIE enabled
- `/system/bin/linker64` - Android Bionic linker
- **NOT** `/lib/ld-musl-aarch64.so.1`
- **NOT** `/lib64/ld-linux-aarch64.so.1`

#### 4. Verify with readelf

```bash
readelf -h /tmp/test-android | grep "Machine:\|Type:"
readelf -l /tmp/test-android | grep -i "interpreter"
readelf -d /tmp/test-android | grep "NEEDED"
```

Expected:
```
  Type:                              DYN (Position-Independent Executable file)
  Machine:                           AArch64
      [Requesting program interpreter: /system/bin/linker64]
 0x0000000000000001 (NEEDED)       Shared library: [libdl.so]
 0x0000000000000001 (NEEDED)       Shared library: [libc.so]
```

## NDK Version Compatibility

| NDK Version | Status | Notes |
|-------------|--------|-------|
| r27c | Recommended | Latest stable, best Android 14 support |
| r26d | Supported | Good stability |
| r25c | Supported | Minimum recommended |
| r24 | Not tested | May work |
| r23 | Not recommended | Older, less tested |

## API Level Selection

| API Level | Android Version | Notes |
|-----------|----------------|-------|
| 29 | Android 10 | Minimum supported |
| 30 | Android 11 | |
| 31 | Android 12 | |
| 33 | Android 13 | |
| 34 | Android 14 | Recommended target |

The build system defaults to API 29 for maximum compatibility. You can override:

```bash
export API_LEVEL=34
```

## Troubleshooting

### "ANDROID_NDK not set"

**Problem**: Environment variable not configured.

**Solution**:
```bash
echo 'export ANDROID_NDK=/opt/android-ndk-r27c' >> ~/.bashrc
source ~/.bashrc
echo $ANDROID_NDK  # Should show path
```

---

### "clang: command not found"

**Problem**: Toolchain not in PATH.

**Solution**:
```bash
# Use full path or add to PATH
export PATH=$ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH

# Verify
which aarch64-linux-android29-clang
```

---

### "cannot find -lc" or missing libc

**Problem**: Sysroot not properly detected.

**Solution**:
```bash
# Explicitly set sysroot
export SYSROOT=$ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/sysroot
export CFLAGS="--sysroot=$SYSROOT"
export LDFLAGS="--sysroot=$SYSROOT"
```

---

### NDK Download Fails

**Problem**: Network or disk space issues.

**Solution**:
```bash
# Check disk space
df -h /opt

# Check if download completed
ls -lh /tmp/android-ndk-r27c-linux.zip

# Alternative: Download via browser and copy
cp ~/Downloads/android-ndk-r27c-linux.zip /tmp/
cd /tmp && unzip -q android-ndk-r27c-linux.zip -d /opt/
```

---

### Permission Denied

**Problem**: NDK directory not writable.

**Solution**:
```bash
sudo chown -R $(whoami):$(whoami) $ANDROID_NDK
```

---

### Wrong Architecture Output

**Problem**: Compiler produces x86_64 binaries instead of ARM64.

**Solution**: Verify you're using the aarch64 compiler:
```bash
# WRONG
$ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/clang

# CORRECT
$ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android29-clang
```

---

## Next Steps

Once NDK is set up:

1. **Build the full repository**: `./build.sh all`
2. **Build specific packages**: `./build.sh pkg <name>`
3. **Create custom NDK builds**: See `build/ndk-scripts/` for examples

See [BUILD_GUIDE.md](BUILD_GUIDE.md) for detailed package building instructions.
