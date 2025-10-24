# Publishing Guide for olakai-sdk

This guide provides comprehensive instructions for publishing new versions of the olakai-sdk package to PyPI.

## Prerequisites

### 1. PyPI Account Setup
- Create an account at https://pypi.org
- Create an organization (if needed)
- Create a project named `olakai-sdk`

### 2. API Token Setup
- Go to https://pypi.org/manage/account/token/
- Click "Add API token"
- Name it (e.g., "olakai-sdk-upload")
- Set scope to "Project: olakai-sdk" (recommended) or "Entire account"
- Copy the token (starts with `pypi-...`)

### 3. Configure Credentials

Create or update `~/.pypirc` with your API token:

```ini
[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN_HERE
```

Set secure permissions:
```bash
chmod 600 ~/.pypirc
```

### 4. Install Build Tools

Install required tools (if not already installed):
```bash
pip install --upgrade build twine
```

## Publishing a New Version

### Step 1: Update Version Number

Edit `pyproject.toml` and update the version number:
```toml
[project]
name = "olakai-sdk"
version = "0.4.1"  # Update this line
```

Version numbering follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version (1.0.0): Breaking changes
- **MINOR** version (0.5.0): New features, backward compatible
- **PATCH** version (0.4.1): Bug fixes, backward compatible

### Step 2: Update Changelog (Recommended)

Document changes in your changelog or release notes.

### Step 3: Commit Changes

```bash
git add pyproject.toml
git commit -m "Bump version to 0.4.1"
```

### Step 4: Clean Previous Builds

Remove old distribution files:
```bash
rm -rf dist/ build/ src/*.egg-info
```

### Step 5: Build Distribution Packages

```bash
python3 -m build
```

This creates:
- `dist/olakai_sdk-X.Y.Z-py3-none-any.whl` (wheel distribution)
- `dist/olakai_sdk-X.Y.Z.tar.gz` (source distribution)

### Step 6: Validate Packages

Check that packages are correctly formatted:
```bash
python3 -m twine check dist/*
```

You should see:
```
Checking dist/olakai_sdk-X.Y.Z-py3-none-any.whl: PASSED
Checking dist/olakai_sdk-X.Y.Z.tar.gz: PASSED
```

### Step 7: Upload to PyPI

Upload the packages:
```bash
python3 -m twine upload dist/*
```

If credentials are configured in `~/.pypirc`, the upload will proceed automatically.

### Step 8: Verify Upload

Visit your package page:
```
https://pypi.org/project/olakai-sdk/
```

Test installation in a clean environment:
```bash
pip install --upgrade olakai-sdk
```

### Step 9: Tag the Release (Recommended)

Create a git tag for the release:
```bash
git tag -a v0.4.1 -m "Release version 0.4.1"
git push origin v0.4.1
```

## Testing Before Production Release

### Option 1: TestPyPI

To test the upload process without affecting the production package:

1. Create a TestPyPI account at https://test.pypi.org
2. Get a TestPyPI API token
3. Add TestPyPI credentials to `~/.pypirc`:

```ini
[testpypi]
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

4. Upload to TestPyPI:
```bash
python3 -m twine upload --repository testpypi dist/*
```

5. Test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ olakai-sdk
```

### Option 2: Local Testing

Test the built package locally before uploading:

```bash
# Install from local wheel
pip install dist/olakai_sdk-X.Y.Z-py3-none-any.whl

# Or install in editable mode during development
pip install -e .
```

## Quick Reference Commands

```bash
# One-liner for publishing (after updating version)
rm -rf dist/ build/ src/*.egg-info && python3 -m build && python3 -m twine check dist/* && python3 -m twine upload dist/*

# Upload specific version only
python3 -m twine upload dist/olakai_sdk-0.4.1*
```

## Troubleshooting

### Authentication Issues

If you get authentication errors:
- Verify your token is correct in `~/.pypirc`
- Ensure username is `__token__` (not your PyPI username)
- Check token hasn't expired or been revoked
- Verify token scope includes the project

### File Already Exists Error

If you get "File already exists" error:
- You cannot re-upload the same version
- Increment the version number in `pyproject.toml`
- Rebuild and upload again

### Build Errors

If build fails:
- Check `pyproject.toml` syntax
- Ensure all required files exist (README.md, LICENSE, etc.)
- Verify source code has no syntax errors

### Network Issues

If upload times out or fails:
- Check your internet connection
- Retry the upload (twine is idempotent)
- Use `--verbose` flag for more details: `python3 -m twine upload --verbose dist/*`

## Package Information

- **Package name on PyPI**: `olakai-sdk`
- **Import name**: `olakaisdk`
- **Installation**: `pip install olakai-sdk`
- **Usage**: `from olakaisdk import olakai_config, olakai_monitor`

## Security Best Practices

1. **Never commit** `.pypirc` or API tokens to git
2. Add `~/.pypirc` to your global `.gitignore`
3. Use **project-scoped tokens** instead of account-wide tokens
4. Rotate tokens periodically
5. Use different tokens for different projects
6. Keep `~/.pypirc` permissions at 600 (readable only by you)

## Additional Resources

- PyPI Help: https://pypi.org/help/
- Python Packaging Guide: https://packaging.python.org/
- Twine Documentation: https://twine.readthedocs.io/
- Semantic Versioning: https://semver.org/

## Publishing History

- **v0.4.0** - 2024-10-24 - Initial PyPI release with simplified API
