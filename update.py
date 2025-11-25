"""
DuckyTrading Auto-Updater
Pulls latest code from GitHub and rebuilds the application
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


class AutoUpdater:
    """Handle automatic updates from GitHub."""
    
    def __init__(self):
        self.repo_path = Path(__file__).parent
        self.backup_path = self.repo_path / "DuckyTrading.exe.backup"
        self.exe_path = self.repo_path / "dist" / "DuckyTrading" / "DuckyTrading.exe"
        
    def print_header(self, text):
        """Print a formatted header."""
        print("\n" + "=" * 50)
        print(f"   {text}")
        print("=" * 50 + "\n")
        
    def check_git_installed(self):
        """Check if git is installed."""
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ ERROR: Git is not installed or not in PATH")
            print("Please install Git from: https://git-scm.com/download/win")
            return False
            
    def check_is_git_repo(self):
        """Check if current directory is a git repository."""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            print("❌ ERROR: Not a git repository")
            print("Please run this from the DuckyTrading folder")
            return False
        return True
        
    def check_for_updates(self):
        """Check if updates are available."""
        print("[1/5] 🔍 Checking for updates...")
        
        # Fetch latest from origin
        try:
            subprocess.run(
                ["git", "fetch", "origin", "master"],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to fetch updates: {e}")
            return False
            
        # Check if there are differences
        try:
            result = subprocess.run(
                ["git", "diff", "--quiet", "HEAD", "origin/master"],
                cwd=self.repo_path,
                capture_output=True
            )
            
            if result.returncode == 0:
                print("✅ You already have the latest version!")
                return False
            else:
                print("🆕 Updates available!")
                return True
                
        except subprocess.CalledProcessError:
            return True
            
    def show_changelog(self):
        """Show what's new in the update."""
        print("\n" + "=" * 50)
        print("   What's New:")
        print("=" * 50)
        
        try:
            result = subprocess.run(
                ["git", "log", "HEAD..origin/master", "--oneline", "--decorate"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                print(result.stdout)
            else:
                print("No commit messages available.")
                
        except subprocess.CalledProcessError:
            print("Could not retrieve changelog.")
            
    def confirm_update(self):
        """Ask user to confirm update."""
        while True:
            response = input("\nDo you want to update? (Y/N): ").strip().upper()
            if response in ['Y', 'YES']:
                return True
            elif response in ['N', 'NO']:
                print("Update cancelled.")
                return False
            else:
                print("Please enter Y or N")
                
    def backup_current(self):
        """Backup current executable."""
        print("\n[2/5] 💾 Backing up current version...")
        
        if self.backup_path.exists():
            self.backup_path.unlink()
            
        if self.exe_path.exists():
            try:
                shutil.copy2(self.exe_path, self.backup_path)
                print(f"✅ Backup created: {self.backup_path.name}")
                return True
            except Exception as e:
                print(f"⚠️  Warning: Could not create backup: {e}")
                return False
        else:
            print("ℹ️  No existing executable to backup")
            return True
            
    def pull_updates(self):
        """Pull latest code from GitHub."""
        print("\n[3/5] 📥 Pulling latest code from GitHub...")
        
        try:
            result = subprocess.run(
                ["git", "pull", "origin", "master"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ Code updated successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to pull updates: {e}")
            print(e.stderr)
            return False
            
    def install_dependencies(self):
        """Install/update Python dependencies."""
        print("\n[4/5] 📦 Installing/updating dependencies...")
        
        requirements_file = self.repo_path / "requirements.txt"
        if not requirements_file.exists():
            print("⚠️  requirements.txt not found, skipping...")
            return True
            
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"],
                cwd=self.repo_path,
                check=True
            )
            print("✅ Dependencies updated")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Some dependencies failed to install")
            print("The app may still work, but check for errors")
            return True  # Continue anyway
            
    def rebuild_app(self):
        """Rebuild the application."""
        print("\n[5/5] 🔨 Rebuilding application...")
        
        package_script = self.repo_path / "package_app.py"
        if not package_script.exists():
            print("❌ package_app.py not found")
            return False
            
        try:
            subprocess.run(
                [sys.executable, "package_app.py"],
                cwd=self.repo_path,
                check=True
            )
            print("✅ Application rebuilt successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            if self.backup_path.exists():
                print(f"Your backup is available: {self.backup_path}")
            return False
            
    def run(self):
        """Run the update process."""
        self.print_header("DuckyTrading Auto-Updater")
        
        # Prechecks
        if not self.check_git_installed():
            return False
            
        if not self.check_is_git_repo():
            return False
            
        # Check for updates
        if not self.check_for_updates():
            return True  # Already up to date
            
        # Show changelog
        self.show_changelog()
        
        # Confirm
        if not self.confirm_update():
            return True
            
        # Backup
        self.backup_current()
        
        # Pull updates
        if not self.pull_updates():
            return False
            
        # Install dependencies
        self.install_dependencies()
        
        # Rebuild
        if not self.rebuild_app():
            return False
            
        # Success
        self.print_header("Update Complete!")
        print("✅ Your app has been updated successfully.")
        print(f"📂 You can now run: dist/DuckyTrading/DuckyTrading.exe")
        print("\nℹ️  Note: Your .env and credentials are preserved.")
        
        return True


if __name__ == "__main__":
    updater = AutoUpdater()
    success = updater.run()
    
    print("\nPress Enter to exit...")
    input()
    
    sys.exit(0 if success else 1)
