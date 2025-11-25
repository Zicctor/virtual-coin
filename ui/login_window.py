"""Binance-style login window with Google OAuth."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon, QColor
import sys
import os


class LoginWindow(QWidget):
    """Modern Binance-style login window."""
    
    # Signal emitted when login is successful
    login_successful = pyqtSignal(dict, object)  # Emits (user_info dict, db_user dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Ducky Trading - Login")
        self.setFixedSize(450, 600)
        
        # Set window icon
        icon_path = self.get_icon_path('app_icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setStyleSheet(self.get_stylesheet())
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Create login content
        content = self.create_content()
        main_layout.addWidget(content, 1)
        
        # Create footer
        footer = self.create_footer()
        main_layout.addWidget(footer)
        
        self.setLayout(main_layout)
        
        # Center window on screen
        self.center_on_screen()
    
    def create_header(self):
        """Create the header section."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(80)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(30, 0, 30, 0)
        
        # Logo/Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        # Add bitcoin icon if available
        bitcoin_icon_path = self.get_icon_path('bitcoin_icon.png')
        if os.path.exists(bitcoin_icon_path):
            icon_label = QLabel()
            icon_pixmap = QPixmap(bitcoin_icon_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setStyleSheet("background: transparent;")
            title_layout.addWidget(icon_label)
        
        title = QLabel("DuckyTrading")
        title.setObjectName("logo")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("background: transparent;")  # Fix gray background
        title_layout.addWidget(title)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        header.setLayout(layout)
        return header
    
    def create_content(self):
        """Create the main content area."""
        content = QFrame()
        content.setObjectName("content")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Welcome text
        welcome_label = QLabel("Welcome Back!")
        welcome_label.setObjectName("welcomeTitle")
        welcome_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Sign in to start trading")
        subtitle.setObjectName("subtitle")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(welcome_label)
        layout.addWidget(subtitle)
        
        # Add spacing
        layout.addSpacing(30)
        
        # Google Sign-In Button
        google_btn = QPushButton("Sign in with Google")
        google_btn.setObjectName("googleButton")
        
        # Add Google icon if available
        google_icon_path = self.get_icon_path('google_icon.png')
        if os.path.exists(google_icon_path):
            google_btn.setIcon(QIcon(google_icon_path))
            google_btn.setIconSize(QSize(24, 24))
        
        google_btn.setFixedHeight(50)
        google_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        google_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        google_btn.clicked.connect(self.on_google_login)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 2)
        google_btn.setGraphicsEffect(shadow)
        
        layout.addWidget(google_btn)
        
        # Divider
        layout.addSpacing(20)
        
        # Info text
        info_label = QLabel("Secure authentication powered by Google")
        info_label.setObjectName("infoLabel")
        info_label.setFont(QFont("Segoe UI", 9))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(info_label)
        layout.addStretch()
        
        content.setLayout(layout)
        return content
    
    def create_footer(self):
        """Create the footer section."""
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setFixedHeight(60)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        footer_text = QLabel("© 2025 DuckyTrading. All rights reserved.")
        footer_text.setObjectName("footerText")
        footer_text.setFont(QFont("Segoe UI", 9))
        footer_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(footer_text)
        footer.setLayout(layout)
        return footer
    
    def on_google_login(self):
        """Handle Google login button click."""
        from auth.google_auth import GoogleAuthManager
        
        # Update button state
        sender = self.sender()
        sender.setEnabled(False)
        sender.setText("Authenticating...")
        
        try:
            auth_manager = GoogleAuthManager()
            
            # Force new login to allow account selection
            # This ensures you can choose which Google account to use
            print("🔑 Starting authentication flow...")
            if auth_manager.authenticate(force_new_login=True):
                user_info = auth_manager.get_user_info()
                db_user = auth_manager.get_db_user()
                self.login_successful.emit(user_info, db_user)
            else:
                sender.setText("Sign in with Google")
                sender.setEnabled(True)
                self.show_error("Authentication failed. Please try again.")
        
        except FileNotFoundError as e:
            sender.setText("Sign in with Google")
            sender.setEnabled(True)
            self.show_error(str(e))
        
        except Exception as e:
            sender.setText("Sign in with Google")
            sender.setEnabled(True)
            self.show_error(f"An error occurred: {str(e)}")
    
    def show_error(self, message):
        """Show error message."""
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Authentication Error")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def get_icon_path(self, icon_name):
        """Get the absolute path to an icon file."""
        # Get the directory of this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to pyqt_crypto_app, then to assets/icons
        icon_path = os.path.join(current_dir, '..', 'assets', 'icons', icon_name)
        return os.path.abspath(icon_path)
    
    def center_on_screen(self):
        """Center the window on the screen."""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def get_stylesheet(self):
        """Return the stylesheet for Binance-style dark theme."""
        return """
            QWidget {
                background-color: #0B0E11;
                color: #EAECEF;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            #header {
                background-color: #1E2329;
                border-bottom: 1px solid #2B3139;
            }
            
            #logo {
                color: #F0B90B;
            }
            
            #content {
                background-color: #0B0E11;
            }
            
            #welcomeTitle {
                color: #FFFFFF;
            }
            
            #subtitle {
                color: #848E9C;
            }
            
            #googleButton {
                background-color: #FFFFFF;
                color: #000000;
                border: none;
                border-radius: 4px;
                padding: 12px 24px;
                font-weight: 500;
            }
            
            #googleButton:hover {
                background-color: #F5F5F5;
            }
            
            #googleButton:pressed {
                background-color: #E8E8E8;
            }
            
            #googleButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
            
            #infoLabel {
                color: #848E9C;
            }
            
            #footer {
                background-color: #1E2329;
                border-top: 1px solid #2B3139;
            }
            
            #footerText {
                color: #848E9C;
            }
        """
