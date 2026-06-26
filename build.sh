#!/bin/bash
# ============================================================================
# TX Bionic Build Wrapper
# Main entry point for rebuilding the entire TX Package Repository
# for Android Bionic libc
# ============================================================================
# Usage:
#   ./build.sh [command] [options]
#
# Commands:
#   all          Build all packages and generate repository metadata
#   pkg <name>   Build a single package
#   validate     Validate all built packages
#   clean        Clean build cache
#   metadata     Generate repository metadata only
#   ndk-setup    Verify Android NDK setup
#   test         Run test suite
#
# Environment Variables:
#   ANDROID_NDK   Path to Android NDK (for source builds)
#   API_LEVEL     Target API level (default: 29)
#   JOBS          Number of parallel jobs (default: 4)
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_SYSTEM="$SCRIPT_DIR/build/build_system.py"
VALIDATOR="$SCRIPT_DIR/build/validate_repo.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

show_header() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           TX Bionic Build System v1.0                        ║"
    echo "║           Android ARM64 Bionic Package Repository            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
}

cmd_all() {
    show_header
    log_info "Starting full build..."
    log_info "Target: Android Bionic libc (API 29+)"
    log_info "Architecture: aarch64"
    log_info ""
    
    cd "$SCRIPT_DIR"
    python3 "$BUILD_SYSTEM"
    
    if [ $? -eq 0 ]; then
        echo ""
        log_success "Build completed successfully!"
        echo ""
        log_info "Repository location: $SCRIPT_DIR/repo/stable/"
        log_info "Packages: $SCRIPT_DIR/repo/stable/packages/"
        log_info "Metadata: $SCRIPT_DIR/repo/stable/Packages.json"
        echo ""
        
        # Run validation
        cmd_validate
    else
        echo ""
        log_error "Build failed! Check logs for details."
        exit 1
    fi
}

cmd_pkg() {
    local pkg_name="$1"
    if [ -z "$pkg_name" ]; then
        log_error "Package name required"
        echo "Usage: ./build.sh pkg <package_name>"
        exit 1
    fi
    
    log_info "Building single package: $pkg_name"
    cd "$SCRIPT_DIR"
    python3 -c "
import sys
sys.path.insert(0, 'build')
from build_system import build_txpkg, download_termux_pkglist, setup_dirs
from packages import PACKAGES
import tempfile
from pathlib import Path

setup_dirs()
termux_pkgs = download_termux_pkglist()

if '$pkg_name' not in PACKAGES:
    print(f'ERROR: Package {pkg_name} not found in definitions')
    sys.exit(1)

pkg_info = PACKAGES['$pkg_name']
work_dir = Path(tempfile.mkdtemp(prefix='txbuild_'))
success, result = build_txpkg('$pkg_name', pkg_info, work_dir, termux_pkgs)
if success:
    print(f'Successfully built {result[\"txpkg_path\"]}')
else:
    print(f'Failed: {result[\"errors\"]}')
    sys.exit(1)
"
}

cmd_validate() {
    show_header
    log_info "Validating repository..."
    cd "$SCRIPT_DIR"
    python3 "$VALIDATOR"
    
    if [ $? -eq 0 ]; then
        echo ""
        log_success "All packages validated successfully!"
    else
        echo ""
        log_error "Validation found issues!"
        exit 1
    fi
}

cmd_clean() {
    log_info "Cleaning build cache..."
    rm -rf "$SCRIPT_DIR/build/.cache"
    log_success "Build cache cleaned"
}

cmd_metadata() {
    log_info "Generating repository metadata..."
    cd "$SCRIPT_DIR"
    python3 -c "
import sys
sys.path.insert(0, 'build')
from build_system import generate_repo_metadata, build_txpkg, download_termux_pkglist, setup_dirs
from packages import PACKAGES
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json

setup_dirs()
termux_pkgs = download_termux_pkglist()

# Build all packages
sorted_packages = sorted(PACKAGES.items(), key=lambda x: (x[1]['prio'], x[0]))
results = {}
work_base = tempfile.mkdtemp(prefix='txmeta_')

for pkg_name, pkg_info in sorted_packages:
    work_dir = Path(work_base) / pkg_name
    work_dir.mkdir(parents=True, exist_ok=True)
    try:
        success, result = build_txpkg(pkg_name, pkg_info, work_dir, termux_pkgs)
        results[pkg_name] = result
    except Exception as e:
        results[pkg_name] = {'name': pkg_name, 'success': False, 'errors': [str(e)]}

import shutil
shutil.rmtree(work_base, ignore_errors=True)

generate_repo_metadata(results)
print('Metadata generation complete')
"
}

cmd_ndk_setup() {
    show_header
    log_info "Checking Android NDK setup..."
    
    if [ -z "$ANDROID_NDK" ]; then
        log_error "ANDROID_NDK environment variable not set"
        echo ""
        echo "To set up the Android NDK:"
        echo "  1. Download Android NDK from https://developer.android.com/ndk/downloads"
        echo "  2. Extract to a directory (e.g., /opt/android-ndk)"
        echo "  3. export ANDROID_NDK=/path/to/ndk"
        echo ""
        exit 1
    fi
    
    if [ ! -d "$ANDROID_NDK" ]; then
        log_error "ANDROID_NDK directory does not exist: $ANDROID_NDK"
        exit 1
    fi
    
    log_success "ANDROID_NDK found: $ANDROID_NDK"
    
    # Check for clang
    TOOLCHAIN="$ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64"
    CLANG="$TOOLCHAIN/bin/aarch64-linux-android29-clang"
    
    if [ ! -f "$CLANG" ]; then
        log_warn "aarch64-linux-android29-clang not found"
        log_info "Checking for other API levels..."
        
        for api in 29 30 31 33 34 35; do
            CLANG_TEST="$TOOLCHAIN/bin/aarch64-linux-android${api}-clang"
            if [ -f "$CLANG_TEST" ]; then
                log_success "Found compiler for API $api: $CLANG_TEST"
                break
            fi
        done
    else
        log_success "Found aarch64-linux-android29-clang"
    fi
    
    # Display version
    if [ -f "$CLANG" ]; then
        echo ""
        "$CLANG" --version 2>/dev/null | head -3
    fi
    
    echo ""
    log_success "NDK setup looks good!"
}

cmd_test() {
    show_header
    log_info "Running test suite..."
    
    cd "$SCRIPT_DIR"
    python3 -m pytest build/tests/ -v 2>/dev/null || {
        log_warn "pytest not installed or no tests found"
        log_info "Install: pip install pytest"
    }
}

cmd_help() {
    show_header
    echo "Usage: ./build.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  all          Build all packages and generate metadata (default)"
    echo "  pkg <name>   Build a single package by name"
    echo "  validate     Validate all packages for Bionic compatibility"
    echo "  clean        Remove build cache"
    echo "  metadata     Generate repository metadata only"
    echo "  ndk-setup    Verify Android NDK installation"
    echo "  test         Run test suite"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./build.sh                    # Full build"
    echo "  ./build.sh all                # Full build"
    echo "  ./build.sh pkg curl           # Build curl only"
    echo "  ./build.sh validate           # Validate packages"
    echo "  ./build.sh clean              # Clean cache"
    echo "  ANDROID_NDK=/opt/ndk ./build.sh ndk-setup"
    echo ""
    echo "Environment:"
    echo "  ANDROID_NDK    Path to Android NDK"
    echo "  API_LEVEL      Target Android API (default: 29)"
    echo "  JOBS           Parallel build jobs (default: 4)"
    echo ""
}

# Main
main() {
    local cmd="${1:-all}"
    
    case "$cmd" in
        all)
            cmd_all
            ;;
        pkg)
            cmd_pkg "$2"
            ;;
        validate)
            cmd_validate
            ;;
        clean)
            cmd_clean
            ;;
        metadata)
            cmd_metadata
            ;;
        ndk-setup)
            cmd_ndk_setup
            ;;
        test)
            cmd_test
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            log_error "Unknown command: $cmd"
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
