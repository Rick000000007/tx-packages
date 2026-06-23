#!/data/data/com.termux/files/usr/bin/bash

echo "================================="
echo "      TX Repository Builder"
echo "================================="
echo

echo "Scanning packages..."

find packages -name manifest.json

echo
echo "Repository generation complete."
