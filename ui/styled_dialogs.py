"""Custom styled notification dialogs for DuckyTrading."""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont, QIcon


class StyledMessageBox(QDialog):
    """Custom styled message box with Binance-like design."""
    
    def __init__(self, parent, title, message, icon_type="info", buttons="ok"):
        super().__init__(parent)
        self.result_value = False
        self.icon_type = icon_type
        self.init_ui(title, message, buttons)
        
    def init_ui(self, title, message, buttons):
        """Initialize the UI."""
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(420)
        
        # Remove default window frame for custom look
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with icon and title
        header = self.create_header(title)
        layout.addWidget(header)
        
        # Message body
        body = self.create_body(message)
        layout.addWidget(body)
        
        # Buttons
        button_widget = self.create_buttons(buttons)
        layout.addWidget(button_widget)
        
        self.setLayout(layout)
        self.apply_stylesheet()
        
    def create_header(self, title):
        """Create the header section."""
        header = QWidget()
        header.setObjectName("dialogHeader")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Icon based on type
        icon_label = QLabel(self.get_icon())
        icon_label.setFont(QFont("Segoe UI", 24))
        header_layout.addWidget(icon_label)
        
        header_layout.addSpacing(12)
        
        # Title
        title_label = QLabel(title)
        title_label.setObjectName("dialogTitle")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setObjectName("dialogCloseBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        
        header.setLayout(header_layout)
        return header
        
    def create_body(self, message):
        """Create the message body."""
        body = QWidget()
        body.setObjectName("dialogBody")
        body_layout = QVBoxLayout()
        body_layout.setContentsMargins(20, 20, 20, 20)
        
        message_label = QLabel(message)
        message_label.setObjectName("dialogMessage")
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Segoe UI", 11))
        body_layout.addWidget(message_label)
        
        body.setLayout(body_layout)
        return body
        
    def create_buttons(self, buttons):
        """Create button section."""
        button_widget = QWidget()
        button_widget.setObjectName("dialogButtons")
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(20, 15, 20, 20)
        
        if buttons == "ok":
            ok_btn = QPushButton("OK")
            ok_btn.setObjectName("dialogOkBtn")
            ok_btn.setMinimumWidth(100)
            ok_btn.setMinimumHeight(36)
            ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            ok_btn.clicked.connect(self.accept)
            button_layout.addStretch()
            button_layout.addWidget(ok_btn)
            
        elif buttons == "yesno":
            no_btn = QPushButton("No")
            no_btn.setObjectName("dialogNoBtn")
            no_btn.setMinimumWidth(100)
            no_btn.setMinimumHeight(36)
            no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            no_btn.clicked.connect(self.reject)
            
            yes_btn = QPushButton("Yes")
            yes_btn.setObjectName("dialogYesBtn")
            yes_btn.setMinimumWidth(100)
            yes_btn.setMinimumHeight(36)
            yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            yes_btn.clicked.connect(self.accept_yes)
            
            button_layout.addStretch()
            button_layout.addWidget(no_btn)
            button_layout.addSpacing(10)
            button_layout.addWidget(yes_btn)
        
        button_widget.setLayout(button_layout)
        return button_widget
        
    def get_icon(self):
        """Get icon based on type."""
        icons = {
            "success": "✅",
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "question": "❓"
        }
        return icons.get(self.icon_type, "ℹ️")
        
    def accept_yes(self):
        """Accept with yes result."""
        self.result_value = True
        self.accept()
        
    def apply_stylesheet(self):
        """Apply custom stylesheet."""
        self.setStyleSheet("""
            StyledMessageBox {
                background-color: #1E2329;
                border: 1px solid #F0B90B;
                border-radius: 8px;
            }
            
            #dialogHeader {
                background-color: #181A20;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid #2B3139;
            }
            
            #dialogTitle {
                color: #EAECEF;
            }
            
            #dialogCloseBtn {
                background-color: transparent;
                color: #848E9C;
                border: none;
                font-size: 24px;
                font-weight: bold;
                border-radius: 4px;
            }
            
            #dialogCloseBtn:hover {
                background-color: #2B3139;
                color: #EAECEF;
            }
            
            #dialogBody {
                background-color: #1E2329;
            }
            
            #dialogMessage {
                color: #EAECEF;
                line-height: 1.6;
            }
            
            #dialogButtons {
                background-color: #181A20;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                border-top: 1px solid #2B3139;
            }
            
            #dialogOkBtn, #dialogYesBtn {
                background-color: #F0B90B;
                color: #181A20;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 24px;
            }
            
            #dialogOkBtn:hover, #dialogYesBtn:hover {
                background-color: #F8D33A;
            }
            
            #dialogOkBtn:pressed, #dialogYesBtn:pressed {
                background-color: #D9A704;
            }
            
            #dialogNoBtn {
                background-color: transparent;
                color: #EAECEF;
                border: 1px solid #474D57;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 24px;
            }
            
            #dialogNoBtn:hover {
                background-color: #2B3139;
                border: 1px solid #F0B90B;
                color: #F0B90B;
            }
        """)


def show_success(parent, title, message):
    """Show success message."""
    dialog = StyledMessageBox(parent, title, message, "success", "ok")
    dialog.exec()
    
    
def show_info(parent, title, message):
    """Show info message."""
    dialog = StyledMessageBox(parent, title, message, "info", "ok")
    dialog.exec()
    

def show_warning(parent, title, message):
    """Show warning message."""
    dialog = StyledMessageBox(parent, title, message, "warning", "ok")
    dialog.exec()
    

def show_error(parent, title, message):
    """Show error message."""
    dialog = StyledMessageBox(parent, title, message, "error", "ok")
    dialog.exec()
    

def show_question(parent, title, message):
    """Show question dialog. Returns True if Yes, False if No."""
    dialog = StyledMessageBox(parent, title, message, "question", "yesno")
    dialog.exec()
    return dialog.result_value
