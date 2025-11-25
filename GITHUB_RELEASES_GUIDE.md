# GitHub Releases Guide for DuckyTrading

This guide explains how to distribute updates to your friends using GitHub releases.

## Initial Setup (One-time)

### 1. Create GitHub Repository
- Go to https://github.com/Zicctor/virtual-coin
- Repository should be public (so friends can download without GitHub accounts)

### 2. Push Your Code
```powershell
cd z:\virtual_coin\pyqt_crypto_app
git init
git add .
git commit -m "Initial commit v1.0.0"
git branch -M master
git remote add origin https://github.com/Zicctor/virtual-coin.git
git push -u origin master
```

## Creating a New Release

### Step 1: Update Version Number
Edit `version.py`:
```python
VERSION = "1.0.1"  # Increment this
RELEASE_DATE = "2025-11-26"  # Update date
```

### Step 2: Build the Application
```powershell
cd z:\virtual_coin\pyqt_crypto_app
python package_app.py
```

This creates `dist/DuckyTrading/` folder with your app.

### Step 3: Create Release Package
1. Navigate to `dist/` folder
2. Right-click `DuckyTrading` folder → Send to → Compressed (zipped) folder
3. Rename to `DuckyTrading-v1.0.1.zip` (match version number)

### Step 4: Commit and Push Version Change
```powershell
git add version.py
git commit -m "Bump version to 1.0.1"
git push origin master
```

### Step 5: Create GitHub Release
1. Go to https://github.com/Zicctor/virtual-coin/releases
2. Click "Draft a new release"
3. Click "Choose a tag" → Type `v1.0.1` → "Create new tag: v1.0.1 on publish"
4. **Release title:** `DuckyTrading v1.0.1`
5. **Description:** Write what's new:
   ```markdown
   ## What's New
   - Added automatic update checker
   - Fixed daily bonus bug
   - Improved error messages
   
   ## Installation
   1. Download `DuckyTrading-v1.0.1.zip`
   2. Extract the zip file
   3. Run `DuckyTrading.exe`
   
   ## Requirements
   - Get `.env` file from developer (contains database connection)
   ```
6. **Attach files:** Drag `DuckyTrading-v1.0.1.zip` to the upload area
7. Click "Publish release"

## Your Friends' Update Process

When they launch the app:
1. App checks GitHub for new version (happens automatically)
2. If update available, shows popup: "New version available! v1.0.1"
3. They click "Yes" → browser opens to GitHub release page
4. They download `DuckyTrading-v1.0.1.zip`
5. Extract and replace old files with new ones
6. Run `DuckyTrading.exe`

## Quick Reference

### Version Numbering
- **Major** (X.0.0): Breaking changes, complete rewrites
- **Minor** (1.X.0): New features, significant changes
- **Patch** (1.0.X): Bug fixes, small improvements

Examples:
- `1.0.0` → First release
- `1.0.1` → Bug fix
- `1.1.0` → New trading feature added
- `2.0.0` → Major redesign

### Release Checklist
- [ ] Update `version.py` with new version and date
- [ ] Run `python package_app.py` to build
- [ ] Test the built app (run `dist/DuckyTrading/DuckyTrading.exe`)
- [ ] Create zip file: `DuckyTrading-vX.X.X.zip`
- [ ] Commit version change to git
- [ ] Create GitHub release with tag `vX.X.X`
- [ ] Upload zip file to release
- [ ] Write clear release notes
- [ ] Publish release

## Troubleshooting

### "Update available" shows but no new version exists
- Make sure git tag matches version.py: `v1.0.1` in both places
- Check that zip file is uploaded to the release
- Wait a few minutes for GitHub's cache to update

### Friends can't download
- Make sure repository is **public**
- Check that zip file was successfully uploaded
- Share direct link: `https://github.com/Zicctor/virtual-coin/releases/latest`

### App doesn't show update notification
- Update checker runs 2 seconds after app starts
- Check console/terminal for error messages
- Verify internet connection
- Make sure `packaging` library is installed

## Advanced: Automated Releases (Optional)

You can automate the build process with GitHub Actions:

1. Create `.github/workflows/release.yml`:
```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python package_app.py
      - uses: actions/upload-artifact@v3
        with:
          name: DuckyTrading
          path: dist/DuckyTrading/
```

Then just push a tag to trigger automatic build:
```powershell
git tag v1.0.1
git push origin v1.0.1
```

## Security Notes

**Never commit these files:**
- `.env` (contains database password)
- `credentials/token.pickle` (user-specific auth)
- `__pycache__/` (Python cache files)

**Safe to commit:**
- `credentials/client_secret.json` (OAuth app credentials)
- All `.py` source files
- `requirements.txt`
- `README.md` and docs

**Share separately with friends:**
- `.env` file (via secure method like password-protected zip, encrypted message)
- Neon database access (add them as collaborator in Neon console)
