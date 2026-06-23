# TX Package Specification v1.0

## Package Extension

.txpkg

## Archive Format

tar.xz

## Package Layout

manifest.json
payload/
scripts/

## Manifest

Required fields:

- name
- version
- release
- architecture
- license
- description
- homepage
- maintainer
- dependencies

## Installation Prefix

/usr

## Supported Architecture

- aarch64

## Repository Channels

- stable
- testing
- unstable

## Package Manager

pkg

## Repository Index

Packages.json

## Package Integrity

SHA256 checksum verification

## Future Features

- Package signatures
- Delta updates
- Multiple mirrors
