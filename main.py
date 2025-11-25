"""Main application entry point for PyQt6 Crypto Trading App."""
import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from ui.login_window import LoginWindow
from ui.trading_window import TradingWindow
from auth.google_auth import GoogleAuthManager


def check_prerequisites():
    """Check if all prerequisites are met."""
    print("=" * 60)
    print("🚀 DuckyTrading - Starting Application")
    print("=" * 60)
    
    # Check database
    try:
        from check_database import check_database_connection, run_migrations
        if not check_database_connection():
            print("\n⚠️ Database connection warning!")
            print("The app will start but some features may not work.")
            print("Please check your .env file and Supabase configuration.\n")
            # Don't return False - allow app to continue
        else:
            if not run_migrations():
                print("\n⚠️ Database migration required (see SQL above)")
                print("App will continue but daily bonus feature won't work until migration is done.\n")
    except Exception as e:
        print(f"⚠️ Database check failed: {e}")
        print("The app will start anyway...\n")
    
    print("=" * 60)
    return True


class MainWindow(QMainWindow):
    """Main trading window (placeholder for now)."""
    
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.init_ui()
    
    def init_ui(self):
        """Initialize the main trading UI."""
        self.setWindowTitle("DuckyTrading - Trading Platform")
        self.setGeometry(100, 100, 1400, 800)
        
        # Set window icon
        icon_path = self.get_icon_path('app_icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Placeholder content
        central_widget = QLabel(
            f"Welcome, {self.user_info.get('name', 'User')}!\n\n"
            f"Email: {self.user_info.get('email', '')}\n\n"
            "Trading interface coming soon..."
        )
        central_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_widget.setStyleSheet("""
            QLabel {
                background-color: #0B0E11;
                color: #EAECEF;
                font-size: 18px;
                font-family: 'Segoe UI';
            }
        """)
        
        self.setCentralWidget(central_widget)
    
    def get_icon_path(self, icon_name):
        """Get the absolute path to an icon file."""
        # Get the directory of this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go to assets/icons
        icon_path = os.path.join(current_dir, 'assets', 'icons', icon_name)
        return os.path.abspath(icon_path)


class CryptoTradingApp:
    """Main application controller."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')  # Modern look
        
        # Set application icon
        icon_path = self.get_icon_path('app_icon.png')
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
        
        self.login_window = None
        self.main_window = None
        self.auth_manager = GoogleAuthManager()
    
    def start(self):
        """Start the application."""
        # Check if user is already authenticated
        if self.auth_manager.is_authenticated():
            # Fetch user info and sync with database for existing session
            print("🔑 Found existing authentication token")
            self.auth_manager._fetch_user_info()
            self.auth_manager._sync_user_to_database()
            
            user_info = self.auth_manager.get_user_info()
            db_user = self.auth_manager.get_db_user()
            
            if user_info and db_user:
                print(f"✅ Auto-login successful: {user_info.get('email', '')}")
                self.show_main_window(user_info, db_user)
            else:
                print("⚠️ Failed to restore session, showing login window")
                self.show_login_window()
        else:
            self.show_login_window()
        
        sys.exit(self.app.exec())
    
    def show_login_window(self):
        """Show the login window."""
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_successful)
        self.login_window.show()
    
    def on_login_successful(self, user_info, db_user):
        """Handle successful login."""
        print(f"Login successful: {user_info.get('email', '')}")
        
        if db_user:
            print(f"Database user loaded: User ID {db_user.get('user_id')}")
        else:
            print("Warning: Database user not found")
        
        # Close login window
        if self.login_window:
            self.login_window.close()
        
        # Show main trading window
        self.show_main_window(user_info, db_user)
    
    def show_main_window(self, user_info, db_user=None):
        """Show the main trading window."""
        # If db_user not provided, try to get it
        if not db_user and self.auth_manager.is_authenticated():
            print("Attempting to get db_user...")
            db_user = self.auth_manager.get_db_user()
        
        print(f"\n{'='*60}")
        print(f"📊 Opening Trading Window")
        print(f"   User: {user_info.get('email', 'Unknown')}")
        print(f"   DB User: {db_user}")
        print(f"{'='*60}\n")
        
        if db_user:
            print(f"✅ Opening TradingWindow for user_id: {db_user.get('user_id')}")
            # Use new trading window
            self.main_window = TradingWindow(user_info, db_user)
            self.main_window.show()
        else:
            print("❌ ERROR: No db_user found - cannot open trading window")
            print("Please check your database configuration in .env file")
            # Show error message
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Database Error")
            msg.setInformativeText("Could not load user data from database.\n\nPlease check:\n1. Database is running\n2. .env configuration is correct\n3. Run reset_database.py if needed")
            msg.setWindowTitle("Error")
            msg.exec()
            sys.exit(1)
    
    def get_icon_path(self, icon_name):
        """Get the absolute path to an icon file."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, 'assets', 'icons', icon_name)
        return os.path.abspath(icon_path)


def main():
    """Application entry point."""
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Application startup failed due to missing prerequisites")
        input("Press Enter to exit...")
        return
    
    app = CryptoTradingApp()
    app.start()


if __name__ == '__main__':
    main()
