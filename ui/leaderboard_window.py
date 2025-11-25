"""Leaderboard window showing user rankings."""
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QTabWidget, QFrame, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon
from utils.db_factory import get_database
from utils.price_service import get_price_service
from config import Config


class LeaderboardWindow(QMainWindow):
    """Leaderboard window showing rankings and stats."""
    
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.db = get_database()
        self.price_service = get_price_service()
        
        self.init_ui()
        self.load_leaderboard()
        
        # Auto refresh every 30 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_leaderboard)
        self.refresh_timer.start(30000)
    
    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("🏆 Leaderboard - Top Traders")
        self.setGeometry(150, 150, 900, 700)
        self.setStyleSheet(self.get_stylesheet())
        
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🏆 Leaderboard")
        header.setObjectName("leaderboardTitle")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)
        
        # Your rank display
        self.rank_widget = self.create_rank_widget()
        main_layout.addWidget(self.rank_widget)
        
        # Tabs for different leaderboards
        tabs = QTabWidget()
        tabs.setObjectName("leaderboardTabs")
        
        # Total Assets Leaderboard
        self.total_table = self.create_leaderboard_table()
        tabs.addTab(self.total_table, "💰 USDT")
        
        # Coin-specific leaderboards - get all non-USDT currencies
        self.coin_currencies = [c for c in Config.DEFAULT_CURRENCIES if c != 'USDT']
        for currency in self.coin_currencies:
            coin_table = self.create_leaderboard_table()
            setattr(self, f'{currency.lower()}_table', coin_table)
            
            # Add tab with coin icon
            icon_path = self.get_icon_path(f"{currency.lower()}.png")
            if os.path.exists(icon_path):
                tabs.addTab(coin_table, QIcon(icon_path), currency)
            else:
                tabs.addTab(coin_table, f"🪙 {currency}")
        
        tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(tabs)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.clicked.connect(self.load_leaderboard)
        main_layout.addWidget(refresh_btn)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def create_rank_widget(self):
        """Create widget showing user's current rank."""
        widget = QFrame()
        widget.setObjectName("rankWidget")
        widget.setFixedHeight(100)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Rank
        rank_layout = QVBoxLayout()
        self.rank_label = QLabel("Your Rank")
        self.rank_label.setObjectName("rankLabel")
        self.rank_value = QLabel("#-")
        self.rank_value.setObjectName("rankValue")
        self.rank_value.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        rank_layout.addWidget(self.rank_label)
        rank_layout.addWidget(self.rank_value)
        layout.addLayout(rank_layout)
        
        layout.addStretch()
        
        # Total Value
        value_layout = QVBoxLayout()
        value_title = QLabel("Total Assets")
        value_title.setObjectName("rankLabel")
        self.value_label = QLabel("$0.00")
        self.value_label.setObjectName("valueLabel")
        self.value_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        value_layout.addWidget(value_title)
        value_layout.addWidget(self.value_label)
        layout.addLayout(value_layout)
        
        layout.addStretch()
        
        # Percentile
        percentile_layout = QVBoxLayout()
        percentile_title = QLabel("Top")
        percentile_title.setObjectName("rankLabel")
        self.percentile_label = QLabel("--%")
        self.percentile_label.setObjectName("percentileLabel")
        self.percentile_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        percentile_layout.addWidget(percentile_title)
        percentile_layout.addWidget(self.percentile_label)
        layout.addLayout(percentile_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_leaderboard_table(self):
        """Create a leaderboard table."""
        table = QTableWidget()
        table.setObjectName("leaderboardTable")
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['Rank', 'User', 'Value', 'Assets'])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Column widths
        table.setColumnWidth(0, 80)
        table.setColumnWidth(1, 250)
        table.setColumnWidth(2, 200)
        
        return table
    
    def load_leaderboard(self):
        """Load leaderboard data."""
        try:
            # Get current prices
            symbols = Config.DEFAULT_CURRENCIES
            symbol_prices = self.price_service.get_multiple_prices([s for s in symbols if s != 'USDT'])
            
            # Convert to pair format for portfolio calculation
            # {'BTC': 98000} -> {'BTC/USDT': 98000}
            prices = {}
            for symbol, price in symbol_prices.items():
                if symbol != 'USDT' and price:
                    prices[f"{symbol}/USDT"] = price
            
            # Get total assets leaderboard
            leaderboard = self.db.get_leaderboard(prices, limit=100)
            self.populate_total_table(leaderboard)
            
            # Update user's rank
            rank_info = self.db.get_user_rank(self.user_id, prices)
            if rank_info.get('rank'):
                self.rank_value.setText(f"#{rank_info['rank']}")
                self.value_label.setText(f"${rank_info['total_value']:,.2f}")
                self.percentile_label.setText(f"{100 - rank_info['percentile']:.1f}%")
            
            # Load current coin leaderboard if on coin tab
            self.on_tab_changed(0)
            
        except Exception as e:
            print(f"Error loading leaderboard: {e}")
    
    def populate_total_table(self, leaderboard):
        """Populate total assets table."""
        self.total_table.setRowCount(len(leaderboard))
        
        for i, entry in enumerate(leaderboard):
            # Rank
            rank_item = QTableWidgetItem(f"#{entry['rank']}")
            rank_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Medal for top 3
            if entry['rank'] == 1:
                rank_item.setForeground(QColor("#FFD700"))  # Gold
            elif entry['rank'] == 2:
                rank_item.setForeground(QColor("#C0C0C0"))  # Silver
            elif entry['rank'] == 3:
                rank_item.setForeground(QColor("#CD7F32"))  # Bronze
            
            # Highlight current user
            if entry['user_id'] == self.user_id:
                rank_item.setBackground(QColor("#2B3139"))
            
            self.total_table.setItem(i, 0, rank_item)
            
            # User name
            name_item = QTableWidgetItem(entry['name'])
            name_item.setFont(QFont("Segoe UI", 11))
            if entry['user_id'] == self.user_id:
                name_item.setBackground(QColor("#2B3139"))
                name_item.setForeground(QColor("#F0B90B"))
            self.total_table.setItem(i, 1, name_item)
            
            # Total value
            value_item = QTableWidgetItem(f"${entry['total_value']:,.2f}")
            value_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            value_item.setForeground(QColor("#0ECB81"))
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if entry['user_id'] == self.user_id:
                value_item.setBackground(QColor("#2B3139"))
            self.total_table.setItem(i, 2, value_item)
            
            # Assets breakdown
            assets = ", ".join([f"{b['currency']}: {b['balance']:.4f}" for b in entry['breakdown'][:3]])
            assets_item = QTableWidgetItem(assets)
            assets_item.setFont(QFont("Segoe UI", 9))
            assets_item.setForeground(QColor("#848E9C"))
            if entry['user_id'] == self.user_id:
                assets_item.setBackground(QColor("#2B3139"))
            self.total_table.setItem(i, 3, assets_item)
            
            self.total_table.setRowHeight(i, 50)
    
    def on_tab_changed(self, index):
        """Handle tab change to load coin-specific leaderboard."""
        if index == 0:
            return  # Total assets already loaded
        
        # Get currency from tab (index - 1 because first tab is Total Assets)
        if index - 1 < len(self.coin_currencies):
            currency = self.coin_currencies[index - 1]
            table = getattr(self, f'{currency.lower()}_table')
            self.load_coin_leaderboard(currency, table)
    
    def get_icon_path(self, icon_name):
        """Get the absolute path to an icon file."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, '..', 'assets', 'icons', icon_name)
        return os.path.abspath(icon_path)
    
    def load_coin_leaderboard(self, currency: str, table: QTableWidget):
        """Load leaderboard for specific coin."""
        try:
            # Get current price for this coin
            pair = f"{currency}/USDT"
            current_price = self.price_service.get_pair_price(pair) or 0
            
            leaderboard = self.db.get_coin_leaderboard(currency, limit=100)
            table.setRowCount(len(leaderboard))
            
            for i, entry in enumerate(leaderboard):
                # Rank
                rank_item = QTableWidgetItem(f"#{entry['rank']}")
                rank_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if entry['rank'] <= 3:
                    colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
                    rank_item.setForeground(QColor(colors[entry['rank'] - 1]))
                
                if entry['user_id'] == self.user_id:
                    rank_item.setBackground(QColor("#2B3139"))
                
                table.setItem(i, 0, rank_item)
                
                # User
                name_item = QTableWidgetItem(entry['name'])
                name_item.setFont(QFont("Segoe UI", 11))
                if entry['user_id'] == self.user_id:
                    name_item.setBackground(QColor("#2B3139"))
                    name_item.setForeground(QColor("#F0B90B"))
                table.setItem(i, 1, name_item)
                
                # Value in USDT
                balance = entry['balance']
                usdt_value = balance * current_price
                value_item = QTableWidgetItem(f"${usdt_value:,.2f}")
                value_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                value_item.setForeground(QColor("#0ECB81"))
                value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if entry['user_id'] == self.user_id:
                    value_item.setBackground(QColor("#2B3139"))
                table.setItem(i, 2, value_item)
                
                # Assets (coin amount)
                assets_item = QTableWidgetItem(f"{balance:.8f} {currency}")
                assets_item.setFont(QFont("Segoe UI", 9))
                assets_item.setForeground(QColor("#848E9C"))
                if entry['user_id'] == self.user_id:
                    assets_item.setBackground(QColor("#2B3139"))
                table.setItem(i, 3, assets_item)
                
                table.setRowHeight(i, 50)
                
        except Exception as e:
            print(f"Error loading coin leaderboard: {e}")
    
    def get_stylesheet(self):
        """Return stylesheet."""
        return """
            QMainWindow {
                background-color: #0B0E11;
            }
            
            #leaderboardTitle {
                color: #F0B90B;
                padding: 20px;
            }
            
            #rankWidget {
                background-color: #181A20;
                border: 2px solid #F0B90B;
                border-radius: 8px;
            }
            
            #rankLabel {
                color: #848E9C;
                font-size: 12px;
            }
            
            #rankValue {
                color: #F0B90B;
            }
            
            #valueLabel {
                color: #0ECB81;
            }
            
            #percentileLabel {
                color: #EAECEF;
            }
            
            #leaderboardTabs::pane {
                background-color: #181A20;
                border: 1px solid #2B3139;
            }
            
            QTabBar::tab {
                background-color: #2B3139;
                color: #848E9C;
                padding: 10px 20px;
                border: none;
                font-size: 13px;
            }
            
            QTabBar::tab:selected {
                background-color: #181A20;
                color: #F0B90B;
                border-bottom: 2px solid #F0B90B;
            }
            
            #leaderboardTable {
                background-color: #181A20;
                color: #EAECEF;
                gridline-color: #2B3139;
                border: none;
            }
            
            QHeaderView::section {
                background-color: #1E2329;
                color: #848E9C;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
            
            #refreshButton {
                background-color: #F0B90B;
                color: #181A20;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            
            #refreshButton:hover {
                background-color: #F8D12F;
            }
        """
