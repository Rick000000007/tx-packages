# TX Repository Guide

## Overview

This guide covers the structure, configuration, and maintenance of the TX Package Repository. The repository is the central distribution point for TX Packages consumed by TX-PKG.

## Repository Structure

```
repo/
`-- stable/
    |-- Packages.json          # Package catalog
    |-- index.json             # Repository metadata
    |-- SHA256SUMS             # Package checksums
    `-- packages/
        |-- *.txpkg            # Package archives
        |-- *.json             # Per-package metadata
        `-- *.sha256           # Per-package checksums
```

## Files

### Packages.json

The package catalog listing all available packages:

```json
{
  "repository": "TX Official Stable",
  "version": 2,
  "format_version": 2,
  "metadata_version": 2,
  "architecture": "aarch64",
  "channel": "stable",
  "packages": [
    {
      "name": "nano",
      "version": "7.2-1",
      "architecture": "aarch64",
      "filename": "nano-7.2-1.aarch64.txpkg",
      "sha256": "abc123...",
      "category": "editors",
      "depends": "musl ncurses-libs ncurses-terminfo",
      "description": "Lightweight terminal text editor"
    }
  ]
}
```

### index.json

Repository metadata:

```json
{
  "repository": "TX Official Repository",
  "format_version": 2,
  "metadata_version": 2,
  "architecture": "aarch64",
  "channel": "stable",
  "url": "https://rick000000007.github.io/tx-packages",
  "packages": 54,
  "generated": "2026-06-26T00:00:00Z",
  "valid_until": "2026-07-26T00:00:00Z"
}
```

### SHA256SUMS

Package checksums for integrity verification:

```
abc123...  packages/nano-7.2-1.aarch64.txpkg
def456...  packages/curl-8.14.1-2.aarch64.txpkg
```

## Channels

Repositories support multiple channels:

| Channel | Purpose |
|---------|---------|
| `stable` | Production-ready packages |
| `testing` | Pre-release quality packages |
| `nightly` | Latest development builds |
| `community` | Community-contributed packages |

## TX-PKG Configuration

Add the repository to TX-PKG via `~/.tx/etc/txpkg/repositories.conf`:

```json
{
  "repositories": [
    {
      "name": "tx-main",
      "url": "https://rick000000007.github.io/tx-packages",
      "channel": "stable",
      "priority": 100,
      "enabled": true
    }
  ]
}
```

## Repository Priorities

When multiple repositories provide the same package, the one with the highest priority is chosen:

| Priority | Use Case |
|----------|----------|
| 100 | Main repository |
| 50 | Default for additional repos |
| 1-49 | Lower-priority mirrors |

## Hosting

### GitHub Pages (Recommended)

1. Create a GitHub repository
2. Push the `repo/` directory to the repository
3. Enable GitHub Pages in repository settings
4. Set the Pages source to the main branch

Repository URL: `https://<username>.github.io/<repo>`

### Self-Hosted

Serve the `repo/` directory via any HTTP server:

```nginx
server {
    listen 80;
    server_name packages.example.com;
    root /var/www/tx-packages/repo;
    autoindex off;
    
    location / {
        add_header Access-Control-Allow-Origin *;
    }
}
```

### CDN

For high-traffic repositories, use a CDN:

1. Upload the `repo/` directory to your CDN
2. Configure the CDN to serve the static files
3. Set the repository URL to your CDN endpoint

## Maintenance

### Adding a Package

1. Place the `.txpkg` file in `repo/stable/packages/`
2. Place the `.json` metadata file alongside it
3. Run the repository metadata generator
4. Commit and push changes

### Removing a Package

1. Remove the `.txpkg` and `.json` files from `repo/stable/packages/`
2. Run the repository metadata generator
3. Commit and push changes

### Updating a Package

1. Build the new version of the package
2. Replace the old `.txpkg` and `.json` files
3. Run the repository metadata generator
4. Commit and push changes

### Regenerating Metadata

Use the provided build script:

```bash
python3 build/build_final.py
```

Or regenerate only metadata:

```bash
python3 build/generate-repo-meta.py
```

## Security

### Checksum Verification

Always verify SHA-256 checksums before publishing:

```bash
sha256sum -c repo/stable/SHA256SUMS
```

### HTTPS

Always serve repositories over HTTPS to prevent man-in-the-middle attacks.

### Future: Signature Support

The repository format is designed for future GPG signature support:

```
repo/stable/
|-- Packages.json
|-- Packages.json.sig       # GPG signature
|-- SHA256SUMS
|-- SHA256SUMS.sig
|-- Release                  # Contains checksums of metadata
|-- Release.sig
`-- packages/
```

This will be activated with the `TX_ENABLE_SIGNATURES` compile-time flag in TX-PKG.

## Troubleshooting

### Package Not Found

- Verify the package is listed in `Packages.json`
- Check the `.txpkg` file exists in `packages/`
- Verify the SHA256SUMS entry matches

### Checksum Mismatch

- Regenerate the repository metadata
- Rebuild the package if the archive was modified

### Client Cannot Sync

- Verify the repository URL is accessible
- Check that `Packages.json` is served correctly
- Ensure HTTPS is properly configured
