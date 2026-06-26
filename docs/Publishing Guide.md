# TX Package Publishing Guide

## Overview

This guide covers the workflow for publishing packages to the TX Package Repository and making them available to TX Terminal users.

## Prerequisites

- Access to the tx-packages GitHub repository
- Git configured with proper credentials
- Build environment set up (see Build Guide)

## Publishing Workflow

### 1. Build Packages

Build all packages or specific packages:

```bash
cd tx-packages
python3 build/build_final.py
```

### 2. Validate the Repository

Run the validator to ensure all packages are correct:

```bash
python3 build/validate-repo.py
```

Expected output:
```
Summary: 54 valid, 0 invalid, 54 total
Repository is consistent.
Validation passed.
```

### 3. Review Changes

Check what will be published:

```bash
git status
git diff repo/stable/Packages.json
```

### 4. Test Installation

Before publishing, test installing packages with TX-PKG:

```bash
# In TX Terminal
pkg update
pkg search <package-name>
pkg info <package-name>
pkg install <package-name>
```

### 5. Commit Changes

```bash
git add repo/stable/
git commit -m "feat: add/update packages

- Added <package-name> <version>
- Updated repository metadata
- Regenerated SHA256SUMS"
```

### 6. Push to GitHub

```bash
git push origin main
```

### 7. Verify GitHub Pages

Wait 1-2 minutes for GitHub Pages to update, then verify:

```bash
curl -s https://rick000000007.github.io/tx-packages/repo/stable/Packages.json | head
curl -s https://rick000000007.github.io/tx-packages/repo/stable/SHA256SUMS | head
```

### 8. Announce

Announce the update to users via:
- TX Terminal in-app notifications
- Release notes on GitHub
- Community channels

## Release Types

### Routine Update

Minor updates, security patches:

```bash
python3 build/build_final.py
git add repo/stable/
git commit -m "chore: routine package updates"
git push
```

### New Package

Adding a new package to the repository:

```bash
# 1. Add package definition to build/build_final.py
# 2. Build
python3 build/build_final.py
# 3. Validate
python3 build/validate-repo.py
# 4. Commit with descriptive message
git add repo/stable/ build/build_final.py
git commit -m "feat: add <package-name> <version>

New package: <description>
Dependencies: <list>
Size: <installed-size>"
git push
```

### Major Update

Bulk updates, new features:

```bash
# 1. Update version in build system
# 2. Build everything
python3 build/build_final.py
# 3. Run full validation
python3 build/validate-repo.py
# 4. Create release commit
git add .
git commit -m "release: TX Packages <version>

Changes:
- <change 1>
- <change 2>

total packages: <count>"
git tag "v<version>"
git push && git push --tags
```

## Versioning

The repository follows semantic versioning:

| Version Change | Meaning |
|---------------|---------|
| Major (X.0.0) | Breaking changes to repository format |
| Minor (x.Y.0) | New packages, significant updates |
| Patch (x.y.Z) | Bug fixes, minor updates |

## GitHub Releases

For major releases, create a GitHub Release:

1. Go to the repository on GitHub
2. Click "Releases" > "Draft a new release"
3. Choose the tag (e.g., `v1.0.0`)
4. Add release notes
5. Publish

## Rollback Procedure

If a published package has issues:

### 1. Revert the Commit

```bash
git revert <commit-hash>
git push
```

### 2. Or Remove the Package

```bash
rm repo/stable/packages/<package>-<version>.*
python3 build/generate-repo-meta.py
git add repo/stable/
git commit -m "fix: remove broken <package>"
git push
```

### 3. Notify Users

```bash
# Create an issue explaining the rollback
git issue create --title "Rollback: <package>" \
  --body "<package> was removed due to <reason>."
```

## Quality Checklist

Before every publish:

- [ ] All packages built successfully
- [ ] Validation passes with 0 invalid packages
- [ ] SHA256SUMS matches all packages
- [ ] Packages.json is consistent with packages/
- [ ] index.json has correct metadata
- [ ] Test installation works in TX Terminal
- [ ] No duplicate packages
- [ ] No placeholder or mock binaries
- [ ] No BusyBox or shell included in packages
- [ ] All packages target aarch64 only

## Automation

### GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish Repository

on:
  push:
    branches: [ main ]
    paths:
      - 'repo/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Validate repository
        run: python3 build/validate-repo.py
      
      - name: Verify checksums
        run: |
          cd repo/stable
          sha256sum -c SHA256SUMS
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python3 build/validate-repo.py || exit 1
```

## Security Considerations

### Package Integrity

- Always verify SHA-256 checksums before publishing
- Never modify `.txpkg` files after hashing
- Use HTTPS for all repository hosting

### Source Verification

- Verify Alpine package signatures when available
- Only use official Alpine mirrors
- Pin specific package versions to prevent unexpected changes

### Access Control

- Limit repository write access to maintainers
- Use branch protection rules on GitHub
- Require code review for changes

## Support

For publishing questions or issues:
- Open an issue: https://github.com/Rick000000007/tx-packages/issues
- Contact: packages@txterminal.dev
