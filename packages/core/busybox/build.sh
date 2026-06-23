#!/system/bin/sh

echo "================================="
echo "TX Package Builder"
echo "================================="

PACKAGE="busybox-1.37.0-1.aarch64.txpkg"

echo
echo "Building $PACKAGE..."

tar -cf "$PACKAGE" \
manifest.json \
install.sh \
remove.sh \
payload

echo
echo "Package created:"
echo "$PACKAGE"
