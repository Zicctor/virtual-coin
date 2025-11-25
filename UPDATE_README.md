# Auto-Updater

Quick and easy way to update DuckyTrading without re-downloading.

## How to Use

### Windows Users:
**Double-click `update.bat`**

That's it! The script will:
1. ✅ Check if updates are available
2. 📋 Show you what's new
3. 💾 Backup your current version
4. 📥 Download latest code
5. 🔨 Rebuild the app automatically

### All Platforms:
```powershell
python update.py
```

## Requirements

- **Git** must be installed
  - Download: https://git-scm.com/download/win
  
- **Python** (if using update.py directly)
  - Already installed if you built the app

- **Original installation was cloned with git**
  - Not just extracted from a zip file

## What Gets Updated

✅ **Updated:**
- All source code (.py files)
- Dependencies (from requirements.txt)
- The executable (DuckyTrading.exe)

❌ **NOT Touched:**
- Your `.env` file (database connection)
- Your `credentials/` folder (Google OAuth)
- Your settings and data

## First Time Setup

If you don't have the app yet:

```powershell
# Clone the repository
git clone https://github.com/Zicctor/virtual-coin.git
cd virtual-coin/pyqt_crypto_app

# Get .env and credentials from developer

# Run the app
dist\DuckyTrading\DuckyTrading.exe
```

## Troubleshooting

**"Git is not installed"**
- Install Git and restart your computer

**"Not a git repository"**
- You downloaded a zip file instead of cloning
- Solution: Delete folder and use `git clone` instead

**"Build failed"**
- Your old version is backed up as `DuckyTrading.exe.backup`
- Check that Python and pip are installed
- Try: `pip install -r requirements.txt`

## Manual Update (Alternative)

If auto-updater doesn't work:

```powershell
git pull origin master
pip install -r requirements.txt
python package_app.py
```
