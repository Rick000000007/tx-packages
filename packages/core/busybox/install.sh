#!/system/bin/sh

echo "================================="
echo "Installing BusyBox"
echo "================================="

echo
echo "Package: busybox"
echo "Version: 1.37.0"

mkdir -p "$HOME/.tx/usr/bin"

cp payload/usr/bin/busybox "$HOME/.tx/usr/bin/busybox"

chmod 755 "$HOME/.tx/usr/bin/busybox"

echo
echo "Installation completed."
