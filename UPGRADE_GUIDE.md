# Upgrading from Pre-1.0.1 Versions

If you have an older version of DuckyTrading (before the auto-updater was added), follow these steps:

## Option 1: Add Auto-Update to Your Current Installation

**If your app was installed with `git clone`:**

1. **Download the bootstrap updater:**
   - Go to: https://raw.githubusercontent.com/Zicctor/virtual-coin/master/pyqt_crypto_app/bootstrap_updater.py
   - Right-click → Save As → Save to your DuckyTrading folder (where `DuckyTrading.exe` is)

2. **Run it:**
   ```powershell
   python bootstrap_updater.py
   ```
   Or just double-click `bootstrap_updater.py`

3. **Done!** 
   - Your app is now updated
   - You now have `update.bat` and `update.py` for future updates
   - Just double-click `update.bat` next time you want to update

**If your app was downloaded as a ZIP file:**

You need to switch to git installation for auto-updates:

1. **Backup your settings:**
   - Copy your `.env` file somewhere safe
   - Copy your `credentials/` folder somewhere safe

2. **Delete the old folder**

3. **Clone fresh from GitHub:**
   ```powershell
   git clone https://github.com/Zicctor/virtual-coin.git
   cd virtual-coin/pyqt_crypto_app
   ```

4. **Restore your settings:**
   - Copy `.env` back to `pyqt_crypto_app/`
   - Copy `credentials/` folder back to `pyqt_crypto_app/`

5. **Build the app:**
   ```powershell
   pip install -r requirements.txt
   python package_app.py
   ```

6. **Run it:**
   ```powershell
   dist\DuckyTrading\DuckyTrading.exe
   ```

7. **Future updates:**
   - Just double-click `update.bat`
   - Or run `python update.py`

## Option 2: Keep Using Manual Updates

If you don't want to use git and prefer manual updates:

1. **Download latest release:**
   - Go to: https://github.com/Zicctor/virtual-coin/releases/latest
   - Download `DuckyTrading-vX.X.X.zip`

2. **Extract the new version**

3. **Copy your settings:**
   - Copy your `.env` from old folder to new folder
   - Copy your `credentials/` folder from old folder to new folder

4. **Delete old folder, use new one**

5. **Future updates:**
   - Repeat this process for each new version

## Which Method Should I Choose?

| Feature | Git Clone + Auto-Update | Manual Download |
|---------|------------------------|-----------------|
| **Update Speed** | ⚡ Fast (just run update.bat) | 🐌 Slow (download, extract, copy) |
| **Requires Git** | ✅ Yes | ❌ No |
| **File Size** | 📦 Small (only downloads changes) | 📦 Large (full download) |
| **Setup Complexity** | 🔧 Medium (one-time git clone) | 🔧 Easy (just extract) |
| **Best For** | Technical users, developers | Non-technical users |

**Recommendation:** Use Git + Auto-Update if you're comfortable with command line. It's much faster for future updates!

## Troubleshooting

**"Git is not installed"**
- Download and install: https://git-scm.com/download/win
- Restart your computer
- Try again

**"I don't know how to use git"**
- Just use Option 2 (Manual Updates)
- It's perfectly fine, just a bit slower

**"The bootstrap updater doesn't work"**
- Your installation was probably from a zip file
- Use the "Clone fresh from GitHub" instructions above
- Or stick with manual updates (Option 2)

**"I lost my .env file"**
- Contact the developer to get a new copy
- You'll need the database connection string

## Need Help?

Contact the developer for:
- `.env` file (database connection)
- `credentials/client_secret.json` (Google OAuth)
- Help with setup
