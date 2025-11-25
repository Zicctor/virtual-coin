"""
Package DuckyTrading as standalone Windows EXE
Requires: pip install pyinstaller
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_section(title):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} is installed")
        return True
    except ImportError:
        print("❌ PyInstaller not found!")
        print("   Install it with: pip install pyinstaller")
        return False

def clean_build_dirs():
    """Clean previous build directories."""
    print_section("Cleaning Previous Builds")
    
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🗑️  Removing {dir_name}/")
            try:
                shutil.rmtree(dir_name)
            except PermissionError:
                print(f"⚠️  Warning: Could not remove {dir_name}/ (files may be in use)")
                print(f"   Please close any running instances and try again")
                return False
    
    # Remove spec file
    if os.path.exists('DuckyTrading.spec'):
        print("🗑️  Removing DuckyTrading.spec")
        os.remove('DuckyTrading.spec')
    
    return True
    
    print("✅ Clean complete")

def create_pyinstaller_command():
    """Create PyInstaller command."""
    print_section("Building EXE with PyInstaller")
    
    # Get icon path
    icon_path = Path('assets/icons/app_icon.png')
    
    # Build command as a list
    cmd = [
        'pyinstaller',
        '--name=DuckyTrading',
        '--windowed',
        '--onedir',  # Create folder with dependencies (default, but explicit)
        '--noupx',  # Don't use UPX compression (can cause issues)
        '--add-data', 'assets;assets',
        '--add-data', 'credentials;credentials',
        '--add-data', '.env;.',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=PyQt6.QtWebEngineWidgets',
        '--hidden-import=psycopg2',
        '--hidden-import=psycopg2._psycopg',
        '--hidden-import=google.auth',
        '--hidden-import=google_auth_oauthlib',
        '--hidden-import=googleapiclient',
        '--hidden-import=dateutil',
        '--hidden-import=pkg_resources.py2_warn',
        '--collect-all', 'PyQt6',
        '--noconfirm',
        'main.py'
    ]
    
    # Add icon if it exists
    if icon_path.exists():
        cmd.insert(3, f'--icon={icon_path}')
    
    print("📦 Running PyInstaller...")
    print(f"\nCommand:\n{' '.join(cmd)}\n")
    
    return cmd

def build_exe():
    """Build the EXE using PyInstaller."""
    cmd = create_pyinstaller_command()
    
    # Run PyInstaller
    result = subprocess.run(cmd, shell=False)
    
    if result.returncode == 0:
        print("\n✅ Build completed successfully!")
        return True
    else:
        print(f"\n❌ Build failed with exit code {result.returncode}")
        return False

def create_readme():
    """Create README for distribution."""
    readme_content = """# DuckyTrading - Crypto Trading Simulator

## Installation & Setup

1. Extract all files to a folder
2. Make sure you have internet connection (required for price data)
3. Run DuckyTrading.exe

## First Time Setup

1. Click "Sign in with Google"
2. Complete Google authentication in browser
3. You'll start with $10,000 USDT

## Features

- 📊 Real-time cryptocurrency prices
- 💱 Buy/sell 16 different cryptocurrencies
- 🤝 P2P trading with other users
- 📈 Portfolio tracking with P&L
- 🏆 Leaderboard rankings
- 📜 Transaction history
- 🎁 Daily login bonus

## Supported Cryptocurrencies

BTC, ETH, OP, BNB, SOL, DOGE, TRX, USDT, XRP, ADA, NEAR, LTC, BCH, XLM, LINK, MATIC

## Troubleshooting

**App won't start:**
- Make sure you have internet connection
- Check Windows Firewall/Antivirus isn't blocking it
- Try running as Administrator

**Login fails:**
- Make sure you allow popup windows
- Complete the authorization in browser
- Check your internet connection

**Prices not loading:**
- Check internet connection
- Wait a few seconds and click refresh
- API rate limits may apply

## Support

For issues or questions, check the logs in the application folder.

© 2025 DuckyTrading. All rights reserved.
"""
    
    dist_dir = Path('dist/DuckyTrading')
    if dist_dir.exists():
        readme_path = dist_dir / 'README.txt'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✅ Created {readme_path}")

def verify_build():
    """Verify the build was successful."""
    print_section("Verifying Build")
    
    exe_path = Path('dist/DuckyTrading/DuckyTrading.exe')
    
    if not exe_path.exists():
        print("❌ DuckyTrading.exe not found!")
        return False
    
    print(f"✅ Found: {exe_path}")
    print(f"   Size: {exe_path.stat().st_size / (1024*1024):.2f} MB")
    
    # Copy .env and credentials to the root of dist folder
    # PyInstaller puts them in _internal, but we need them in the root
    print("\n📋 Copying configuration files...")
    dist_dir = Path('dist/DuckyTrading')
    
    # Copy .env file
    if Path('.env').exists():
        shutil.copy('.env', dist_dir / '.env')
        print("✅ Copied .env to distribution")
    else:
        print("⚠️  Warning: .env file not found!")
    
    # Copy credentials folder
    if Path('credentials').exists():
        if (dist_dir / 'credentials').exists():
            shutil.rmtree(dist_dir / 'credentials')
        shutil.copytree('credentials', dist_dir / 'credentials')
        print("✅ Copied credentials/ to distribution")
    else:
        print("⚠️  Warning: credentials/ folder not found!")
    
    # Verify required files
    print("\n🔍 Verifying required files...")
    required_items = {
        '.env': dist_dir / '.env',
        'credentials/client_secret.json': dist_dir / 'credentials' / 'client_secret.json',
        'assets': dist_dir / '_internal' / 'assets'
    }
    
    all_good = True
    for name, path in required_items.items():
        if path.exists():
            print(f"✅ Found: {name}")
        else:
            print(f"❌ Missing: {name}")
            all_good = False
    
    return all_good

def create_installer_bat():
    """Create a simple installer batch file."""
    bat_content = """@echo off
echo ============================================
echo DuckyTrading Installer
echo ============================================
echo.
echo This will copy DuckyTrading to your Programs folder
echo.
pause

set "INSTALL_DIR=%LOCALAPPDATA%\\DuckyTrading"

echo Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo Copying files...
xcopy /E /I /Y "." "%INSTALL_DIR%"

echo Creating desktop shortcut...
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\\Desktop\\DuckyTrading.lnk');$s.TargetPath='%INSTALL_DIR%\\DuckyTrading.exe';$s.IconLocation='%INSTALL_DIR%\\assets\\icons\\app_icon.png';$s.Save()"

echo.
echo ============================================
echo Installation Complete!
echo ============================================
echo.
echo DuckyTrading has been installed to:
echo %INSTALL_DIR%
echo.
echo A desktop shortcut has been created.
echo.
pause
"""
    
    dist_dir = Path('dist/DuckyTrading')
    if dist_dir.exists():
        installer_path = dist_dir / 'INSTALL.bat'
        with open(installer_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        print(f"✅ Created {installer_path}")

def main():
    """Main packaging workflow."""
    print("=" * 80)
    print("  📦 DuckyTrading EXE Packager")
    print("=" * 80)
    
    # Check PyInstaller
    if not check_pyinstaller():
        input("\nPress Enter to exit...")
        return 1
    
    # Confirm
    print("\n⚠️  This will package DuckyTrading as a standalone EXE")
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Packaging cancelled")
        return 0
    
    # Clean previous builds
    if not clean_build_dirs():
        print("\n❌ Cannot proceed with locked files")
        input("\nPress Enter to exit...")
        return 1
    
    # Build EXE
    if not build_exe():
        input("\nPress Enter to exit...")
        return 1
    
    # Create additional files
    create_readme()
    create_installer_bat()
    
    # Verify
    if not verify_build():
        input("\nPress Enter to exit...")
        return 1
    
    # Success!
    print_section("🎉 SUCCESS!")
    print("\n✅ DuckyTrading.exe has been created successfully!")
    print(f"\n📁 Location: dist/DuckyTrading/")
    print(f"\n📋 Distribution Contents:")
    print("   • DuckyTrading.exe - Main application")
    print("   • assets/ - Icons and images")
    print("   • credentials/ - OAuth credentials")
    print("   • .env - Configuration")
    print("   • README.txt - User guide")
    print("   • INSTALL.bat - Easy installer")
    print(f"\n📦 To distribute:")
    print("   1. Zip the entire dist/DuckyTrading/ folder")
    print("   2. Send the ZIP to users")
    print("   3. Users extract and run INSTALL.bat or DuckyTrading.exe directly")
    print(f"\n⚠️  Important Notes:")
    print("   • Make sure client_secret.json is in credentials/")
    print("   • .env file contains your Neon database URL")
    print("   • Users need internet connection to run")
    print("   • First run may be slow while loading libraries")
    
    print("\n" + "=" * 80)
    input("\nPress Enter to exit...")
    return 0

if __name__ == '__main__':
    sys.exit(main())
