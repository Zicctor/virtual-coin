"""
DuckyTrading Standalone Updater
Download this file and run it in your DuckyTrading folder to update to the latest version.

This is a one-time bootstrapper that will:
1. Pull the latest code (which includes the built-in updater)
2. Rebuild the app
3. Future updates can use the built-in update.bat or update.py
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"   {text}")
    print("=" * 60 + "\n")


def check_git():
    """Check if git is installed."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ERROR: Git is not installed")
        print("\nPlease install Git from: https://git-scm.com/download/win")
        print("Then restart your computer and try again.")
        return False


def check_git_repo():
    """Check if we're in a git repository."""
    if not Path(".git").exists():
        print("❌ ERROR: This is not a git repository")
        print("\nThis means your app was downloaded as a zip file.")
        print("\nTo enable auto-updates, you need to:")
        print("1. Delete your current DuckyTrading folder")
        print("2. Open PowerShell or Command Prompt")
        print("3. Run: git clone https://github.com/Zicctor/virtual-coin.git")
        print("4. Copy your .env and credentials/ folder to the new folder")
        print("5. Run this updater again")
        return False
    return True


def main():
    """Run the bootstrap update."""
    print_header("DuckyTrading Standalone Updater")
    print("This will update your app to the latest version.")
    print("After this update, you can use the built-in update.bat or update.py")
    
    # Check git
    if not check_git():
        input("\nPress Enter to exit...")
        return False
    
    # Check if git repo
    if not check_git_repo():
        input("\nPress Enter to exit...")
        return False
    
    # Confirm
    print("\n⚠️  This will:")
    print("  - Pull latest code from GitHub")
    print("  - Update dependencies")
    print("  - Rebuild the app")
    print("  - Your .env and credentials will NOT be touched")
    
    response = input("\nContinue? (Y/N): ").strip().upper()
    if response not in ['Y', 'YES']:
        print("Update cancelled.")
        input("\nPress Enter to exit...")
        return False
    
    # Backup
    print("\n[1/4] 💾 Creating backup...")
    exe_path = Path("dist/DuckyTrading/DuckyTrading.exe")
    backup_path = Path("DuckyTrading.exe.backup")
    
    if exe_path.exists():
        try:
            shutil.copy2(exe_path, backup_path)
            print(f"✅ Backup created: {backup_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not create backup: {e}")
    
    # Pull
    print("\n[2/4] 📥 Pulling latest code from GitHub...")
    try:
        result = subprocess.run(
            ["git", "pull", "origin", "master"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Code updated")
        if "Already up to date" in result.stdout:
            print("ℹ️  You already have the latest code!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to pull updates: {e}")
        print(e.stderr)
        input("\nPress Enter to exit...")
        return False
    
    # Dependencies
    print("\n[3/4] 📦 Updating dependencies...")
    if Path("requirements.txt").exists():
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"],
                check=True
            )
            print("✅ Dependencies updated")
        except subprocess.CalledProcessError:
            print("⚠️  Warning: Some dependencies failed (app may still work)")
    
    # Rebuild
    print("\n[4/4] 🔨 Rebuilding app...")
    if Path("package_app.py").exists():
        try:
            subprocess.run([sys.executable, "package_app.py"], check=True)
            print("✅ App rebuilt successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            if backup_path.exists():
                print(f"Your backup is available: {backup_path}")
            input("\nPress Enter to exit...")
            return False
    else:
        print("⚠️  package_app.py not found, skipping rebuild")
    
    # Success
    print_header("Update Complete!")
    print("✅ Your app has been updated to the latest version!")
    print("\n📂 You can now run: dist\\DuckyTrading\\DuckyTrading.exe")
    print("\n🎉 For future updates, you can use:")
    print("   - update.bat (double-click)")
    print("   - python update.py")
    print("\nℹ️  Your .env and credentials are safe and unchanged.")
    
    input("\nPress Enter to exit...")
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nUpdate cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
