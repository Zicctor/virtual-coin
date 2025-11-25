"""Main trading window with buy/sell functionality."""
import os
from decimal import Decimal
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QComboBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QTabWidget, QFrame,
                             QSplitter, QScrollArea, QButtonGroup)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon, QColor
from utils.db_factory import get_database
from utils.price_service import get_price_service
from utils.freecrypto_service import get_freecrypto_service
from utils.update_checker import UpdateChecker
from ui.web_chart_widget import CoinGeckoChartWidget
from ui import styled_dialogs
from config import Config
from version import VERSION, APP_NAME


class TradingWindow(QMainWindow):
    """Main trading interface with Binance-style layout."""
    
    # Signal for price updates
    price_updated = pyqtSignal(dict)
    
    def __init__(self, user_info, db_user):
        super().__init__()
        self.user_info = user_info
        self.db_user = db_user
        self.user_id = db_user['user_id']
        
        self.db = get_database()
        self.price_service = get_price_service()
        self.freecrypto_service = get_freecrypto_service()
        
        # Current trading pair and chart settings
        self.current_pair = 'BTC/USDT'
        self.current_prices = {}
        self.chart_interval = '1h'  # Default chart interval
        
        # Price display cycling
        self.price_display_index = 0
        self.price_display_pairs = [f"{coin}/USDT" for coin in Config.DEFAULT_CURRENCIES if coin != 'USDT']
        
        self.init_ui()
        self.load_initial_data()
        
        # Start price update timer
        # With 180-second caching and 60-second updates:
        # - 1 update/minute = 1 API call/minute (well under 50/min limit)
        # - ~1,440 calls/month (well under free tier limits)
        self.price_timer = QTimer()
        self.price_timer.timeout.connect(self.update_prices)
        self.price_timer.start(60000)  # Update every 60 seconds (optimized for efficiency)
        
        # Update immediately
        self.update_prices()
        
        # Check for updates (delayed start to not block UI)
        QTimer.singleShot(2000, self.check_for_updates)
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"{APP_NAME} v{VERSION} - Trading Platform")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set window icon
        icon_path = self.get_icon_path('app_icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Apply Binance-style theme
        self.setStyleSheet(self.get_stylesheet())
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Main tabs for Market and Trading
        self.main_tabs = QTabWidget()
        self.main_tabs.setObjectName("mainTabs")
        
        # Market tab (chart and market data only)
        market_tab = self.create_market_tab()
        self.main_tabs.addTab(market_tab, "📊 Market")
        
        # Portfolio tab (wallet and balances)
        portfolio_tab = self.create_portfolio_tab()
        self.main_tabs.addTab(portfolio_tab, "💼 Portfolio")
        
        # Trading tab (order forms and history)
        trading_tab = self.create_trading_tab()
        self.main_tabs.addTab(trading_tab, "💱 Trading")
        
        # P2P Trading tab
        p2p_tab = self.create_full_p2p_tab()
        self.main_tabs.addTab(p2p_tab, "🤝 P2P Trading")
        
        # Transaction History tab
        history_tab = self.create_history_tab()
        self.main_tabs.addTab(history_tab, "📜 History")
        
        main_layout.addWidget(self.main_tabs)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def create_header(self):
        """Create the header with logo and user info."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(56)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(20)
        
        # Logo - Binance style
        logo_label = QLabel(f"⚡ {APP_NAME}")
        logo_label.setObjectName("logo")
        logo_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(logo_label)
        
        # Version label (small, subtle)
        version_label = QLabel(f"v{VERSION}")
        version_label.setObjectName("versionLabel")
        version_label.setFont(QFont("Segoe UI", 9))
        version_label.setStyleSheet("color: #71757a; padding: 0 10px;")
        layout.addWidget(version_label)
        
        layout.addStretch()
        
        # Current pair display with price
        self.header_pair_label = QLabel(self.current_pair)
        self.header_pair_label.setObjectName("headerPairLabel")
        self.header_pair_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(self.header_pair_label)
        
        self.header_price_label = QLabel("$0.00")
        self.header_price_label.setObjectName("headerPriceLabel")
        self.header_price_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(self.header_price_label)
        
        layout.addSpacing(20)
        
        # User info with icon
        user_label = QLabel(f"👤 {self.user_info.get('name', 'User')[:15]}")
        user_label.setObjectName("userLabel")
        user_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(user_label)
        
        # Daily Bonus button
        daily_bonus_btn = QPushButton("🎁 Daily Bonus")
        daily_bonus_btn.setObjectName("bonusButton")
        daily_bonus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        daily_bonus_btn.clicked.connect(self.claim_daily_bonus)
        layout.addWidget(daily_bonus_btn)
        
        # Leaderboard button
        leaderboard_btn = QPushButton("🏆 Leaderboard")
        leaderboard_btn.setObjectName("leaderboardButton")
        leaderboard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        leaderboard_btn.clicked.connect(self.show_leaderboard)
        layout.addWidget(leaderboard_btn)
        
        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("logoutButton")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
        
        header.setLayout(layout)
        return header
    
    def create_market_panel(self):
        """Create the market pairs panel."""
        panel = QFrame()
        panel.setObjectName("marketPanel")
        panel.setMinimumWidth(280)
        panel.setMaximumWidth(320)
        panel.setMinimumHeight(600)  # Ensure enough height for 16 coins
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Markets")
        title.setObjectName("panelTitle")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Market list
        self.market_table = QTableWidget()
        self.market_table.setObjectName("marketTable")
        self.market_table.setColumnCount(3)
        self.market_table.setHorizontalHeaderLabels(['Pair', 'Price', '24h %'])
        
        # Set column widths properly
        header = self.market_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        # Set initial column widths
        self.market_table.setColumnWidth(0, 120)  # Pair column
        self.market_table.setColumnWidth(1, 140)  # Price column
        
        self.market_table.verticalHeader().setVisible(False)
        self.market_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.market_table.cellClicked.connect(self.on_pair_selected)
        
        # Add trading pairs
        for pair in Config.DEFAULT_TRADING_PAIRS:
            self.add_market_row(pair)
        
        layout.addWidget(self.market_table)
        
        panel.setLayout(layout)
        return panel
    
    def create_market_tab(self):
        """Create the market view tab with chart and market pairs only."""
        tab_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Content splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setHandleWidth(1)
        content_splitter.setChildrenCollapsible(False)
        
        # Left: Market pairs
        left_panel = self.create_market_panel()
        content_splitter.addWidget(left_panel)
        
        # Center: Chart (takes full space)
        center_panel = self.create_chart_panel()
        content_splitter.addWidget(center_panel)
        
        # Set splitter sizes - chart takes most space
        content_splitter.setSizes([300, 1100])
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)
        
        layout.addWidget(content_splitter)
        tab_widget.setLayout(layout)
        return tab_widget
    
    def create_portfolio_tab(self):
        """Create the portfolio tab with wallet balances and total value."""
        tab_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Portfolio header
        header_layout = QHBoxLayout()
        
        portfolio_title = QLabel("💼 My Portfolio")
        portfolio_title.setObjectName("portfolioTitle")
        portfolio_title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header_layout.addWidget(portfolio_title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.clicked.connect(self.force_refresh_all)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Stats cards container
        stats_container = QHBoxLayout()
        stats_container.setSpacing(15)
        
        # Total portfolio value card
        value_card = QFrame()
        value_card.setObjectName("portfolioValueCard")
        value_card.setMaximumHeight(140)
        value_layout = QVBoxLayout()
        value_layout.setContentsMargins(20, 15, 20, 15)
        
        value_label_title = QLabel("Total Portfolio Value")
        value_label_title.setObjectName("valueTitle")
        value_label_title.setFont(QFont("Segoe UI", 12))
        value_layout.addWidget(value_label_title)
        
        self.total_value_label = QLabel("$0.00")
        self.total_value_label.setObjectName("totalValue")
        self.total_value_label.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        value_layout.addWidget(self.total_value_label)
        
        value_card.setLayout(value_layout)
        stats_container.addWidget(value_card)
        
        # Today's P&L card (NEW)
        pnl_card = QFrame()
        pnl_card.setObjectName("pnlCard")
        pnl_card.setMaximumHeight(140)
        pnl_card.setStyleSheet("""
            QFrame#pnlCard {
                background-color: #1E2329;
                border: 1px solid #2B3139;
                border-radius: 8px;
            }
        """)
        pnl_layout = QVBoxLayout()
        pnl_layout.setContentsMargins(20, 15, 20, 15)
        
        pnl_title = QLabel("Today's Profit/Loss")
        pnl_title.setObjectName("valueTitle")
        pnl_title.setFont(QFont("Segoe UI", 12))
        pnl_title.setStyleSheet("color: #848E9C;")
        pnl_layout.addWidget(pnl_title)
        
        self.today_pnl_label = QLabel("$0.00")
        self.today_pnl_label.setObjectName("pnlValue")
        self.today_pnl_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self.today_pnl_label.setStyleSheet("color: #EAECEF;")
        pnl_layout.addWidget(self.today_pnl_label)
        
        self.today_pnl_percent = QLabel("(0.00%)")
        self.today_pnl_percent.setFont(QFont("Segoe UI", 14))
        self.today_pnl_percent.setStyleSheet("color: #848E9C;")
        pnl_layout.addWidget(self.today_pnl_percent)
        
        pnl_card.setLayout(pnl_layout)
        stats_container.addWidget(pnl_card)
        
        # Total P&L card (NEW)
        total_pnl_card = QFrame()
        total_pnl_card.setObjectName("totalPnlCard")
        total_pnl_card.setMaximumHeight(140)
        total_pnl_card.setStyleSheet("""
            QFrame#totalPnlCard {
                background-color: #1E2329;
                border: 1px solid #2B3139;
                border-radius: 8px;
            }
        """)
        total_pnl_layout = QVBoxLayout()
        total_pnl_layout.setContentsMargins(20, 15, 20, 15)
        
        total_pnl_title = QLabel("Total Profit/Loss")
        total_pnl_title.setObjectName("valueTitle")
        total_pnl_title.setFont(QFont("Segoe UI", 12))
        total_pnl_title.setStyleSheet("color: #848E9C;")
        total_pnl_layout.addWidget(total_pnl_title)
        
        self.total_pnl_label = QLabel("$0.00")
        self.total_pnl_label.setObjectName("totalPnlValue")
        self.total_pnl_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self.total_pnl_label.setStyleSheet("color: #EAECEF;")
        total_pnl_layout.addWidget(self.total_pnl_label)
        
        self.total_pnl_percent = QLabel("(0.00%)")
        self.total_pnl_percent.setFont(QFont("Segoe UI", 14))
        self.total_pnl_percent.setStyleSheet("color: #848E9C;")
        total_pnl_layout.addWidget(self.total_pnl_percent)
        
        total_pnl_card.setLayout(total_pnl_layout)
        stats_container.addWidget(total_pnl_card)
        
        layout.addLayout(stats_container)
        
        # Profit Breakdown section (NEW)
        profit_breakdown_title = QLabel("📊 Profit/Loss by Coin")
        profit_breakdown_title.setObjectName("assetsTitle")
        profit_breakdown_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(profit_breakdown_title)
        
        # Profit breakdown table
        self.profit_breakdown_table = QTableWidget()
        self.profit_breakdown_table.setObjectName("profitBreakdownTable")
        self.profit_breakdown_table.setColumnCount(5)
        self.profit_breakdown_table.setHorizontalHeaderLabels(['Coin', 'Holdings', 'Current Value', 'Cost Basis', 'P&L'])
        self.profit_breakdown_table.horizontalHeader().setStretchLastSection(True)
        self.profit_breakdown_table.verticalHeader().setVisible(False)
        self.profit_breakdown_table.setColumnWidth(0, 150)
        self.profit_breakdown_table.setColumnWidth(1, 200)
        self.profit_breakdown_table.setColumnWidth(2, 200)
        self.profit_breakdown_table.setColumnWidth(3, 200)
        self.profit_breakdown_table.setMaximumHeight(250)
        layout.addWidget(self.profit_breakdown_table)
        
        # Assets title
        assets_title = QLabel("Your Assets")
        assets_title.setObjectName("assetsTitle")
        assets_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(assets_title)
        
        # Wallet table (larger, more detailed)
        self.wallet_table = QTableWidget()
        self.wallet_table.setObjectName("portfolioWalletTable")
        self.wallet_table.setColumnCount(3)
        self.wallet_table.setHorizontalHeaderLabels(['Currency', 'Balance', 'Value (USDT)'])
        self.wallet_table.horizontalHeader().setStretchLastSection(True)
        self.wallet_table.verticalHeader().setVisible(False)
        self.wallet_table.setColumnWidth(0, 200)
        self.wallet_table.setColumnWidth(1, 300)
        layout.addWidget(self.wallet_table, 1)
        
        tab_widget.setLayout(layout)
        return tab_widget
    
    def create_trading_tab(self):
        """Create the trading tab with order forms and history."""
        tab_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Buy/Sell forms
        order_forms = self.create_order_forms()
        layout.addWidget(order_forms)
        
        # Trade history
        history_panel = self.create_trade_history_panel()
        layout.addWidget(history_panel, 1)
        
        tab_widget.setLayout(layout)
        return tab_widget
    
    def create_full_p2p_tab(self):
        """Create the full P2P trading tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Peer-to-Peer Trading")
        title.setObjectName("panelTitle")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # P2P trading content
        p2p_content = self.create_p2p_trading_tab()
        layout.addWidget(p2p_content, 1)
        
        tab_widget.setLayout(layout)
        return tab_widget
    
    def create_history_tab(self):
        """Create the transaction history tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📜 Transaction History")
        title.setObjectName("portfolioTitle")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.clicked.connect(self.refresh_transaction_history)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        filter_label = QLabel("Filter:")
        filter_label.setFont(QFont("Segoe UI", 11))
        filter_layout.addWidget(filter_label)
        
        # Create filter button group
        self.history_filter_group = QButtonGroup(self)
        
        all_btn = QPushButton("All")
        all_btn.setObjectName("filterButton")
        all_btn.setCheckable(True)
        all_btn.setChecked(True)
        all_btn.clicked.connect(lambda: self.filter_history("all"))
        self.history_filter_group.addButton(all_btn)
        filter_layout.addWidget(all_btn)
        
        buy_btn = QPushButton("Buy")
        buy_btn.setObjectName("filterButton")
        buy_btn.setCheckable(True)
        buy_btn.clicked.connect(lambda: self.filter_history("buy"))
        self.history_filter_group.addButton(buy_btn)
        filter_layout.addWidget(buy_btn)
        
        sell_btn = QPushButton("Sell")
        sell_btn.setObjectName("filterButton")
        sell_btn.setCheckable(True)
        sell_btn.clicked.connect(lambda: self.filter_history("sell"))
        self.history_filter_group.addButton(sell_btn)
        filter_layout.addWidget(sell_btn)
        
        p2p_btn = QPushButton("P2P Trade")
        p2p_btn.setObjectName("filterButton")
        p2p_btn.setCheckable(True)
        p2p_btn.clicked.connect(lambda: self.filter_history("p2p"))
        self.history_filter_group.addButton(p2p_btn)
        filter_layout.addWidget(p2p_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Transaction history table
        self.history_full_table = QTableWidget()
        self.history_full_table.setObjectName("historyTable")
        self.history_full_table.setColumnCount(7)
        self.history_full_table.setHorizontalHeaderLabels(['Time', 'Type', 'Pair/Trade', 'Amount', 'Price', 'Total', 'Fee'])
        self.history_full_table.horizontalHeader().setStretchLastSection(True)
        self.history_full_table.verticalHeader().setVisible(False)
        self.history_full_table.setColumnWidth(0, 150)
        self.history_full_table.setColumnWidth(1, 80)
        self.history_full_table.setColumnWidth(2, 120)
        self.history_full_table.setColumnWidth(3, 150)
        self.history_full_table.setColumnWidth(4, 120)
        self.history_full_table.setColumnWidth(5, 120)
        layout.addWidget(self.history_full_table, 1)
        
        # Store current filter
        self.current_history_filter = "all"
        
        tab_widget.setLayout(layout)
        return tab_widget
    
    def create_chart_panel(self):
        """Create the chart panel (separated from trading forms)."""
        panel = QFrame()
        panel.setObjectName("chartPanel")
        panel.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Price display
        price_frame = self.create_price_display()
        layout.addWidget(price_frame)
        
        # CoinGecko embedded chart (has built-in interval controls)
        self.chart_widget = CoinGeckoChartWidget()
        self.chart_widget.setMinimumHeight(500)
        self.chart_widget.setMinimumWidth(500)
        layout.addWidget(self.chart_widget, 1)
        
        panel.setLayout(layout)
        return panel
    
    def create_trade_history_panel(self):
        """Create just the trade history table."""
        panel = QFrame()
        panel.setObjectName("historyPanel")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("My Trades")
        title.setObjectName("panelTitle")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Trade history table
        self.trade_history_table = self.create_history_table()
        layout.addWidget(self.trade_history_table, 1)
        
        panel.setLayout(layout)
        return panel
    
    def create_price_display(self):
        """Create the price display area."""
        frame = QFrame()
        frame.setObjectName("priceDisplay")
        frame.setFixedHeight(80)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Price
        price_layout = QVBoxLayout()
        self.price_label_title = QLabel("BTC/USDT")
        self.price_label_title.setObjectName("priceLabel")
        self.price_value = QLabel("$0.00")
        self.price_value.setObjectName("priceValue")
        self.price_value.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        price_layout.addWidget(self.price_label_title)
        price_layout.addWidget(self.price_value)
        layout.addLayout(price_layout)
        
        layout.addStretch()
        
        # 24h Change
        change_layout = QVBoxLayout()
        change_label_title = QLabel("24h Change")
        change_label_title.setObjectName("priceLabel")
        self.change_value = QLabel("+0.00%")
        self.change_value.setObjectName("changeValue")
        self.change_value.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        change_layout.addWidget(change_label_title)
        change_layout.addWidget(self.change_value)
        layout.addLayout(change_layout)
        
        frame.setLayout(layout)
        return frame
    
    def create_chart_controls(self):
        """Create chart interval selector."""
        controls = QFrame()
        controls.setObjectName("chartControls")
        controls.setFixedHeight(45)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Label
        interval_label = QLabel("Interval:")
        interval_label.setObjectName("intervalLabel")
        layout.addWidget(interval_label)
        
        # Interval buttons
        intervals = ['1h', '4h', '1d', '1w']
        self.interval_buttons = {}
        
        for interval in intervals:
            btn = QPushButton(interval)
            btn.setObjectName("intervalButton")
            btn.setCheckable(True)
            btn.setFixedSize(50, 30)
            btn.clicked.connect(lambda checked, i=interval: self.change_chart_interval(i))
            
            if interval == self.chart_interval:
                btn.setChecked(True)
            
            self.interval_buttons[interval] = btn
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Chart type toggle
        type_label = QLabel("Type:")
        type_label.setObjectName("intervalLabel")
        layout.addWidget(type_label)
        
        candlestick_btn = QPushButton("Candlestick")
        candlestick_btn.setObjectName("intervalButton")
        candlestick_btn.setCheckable(True)
        candlestick_btn.setChecked(True)
        candlestick_btn.setFixedSize(90, 30)
        candlestick_btn.clicked.connect(lambda: self.update_chart())
        layout.addWidget(candlestick_btn)
        
        line_btn = QPushButton("Line")
        line_btn.setObjectName("intervalButton")
        line_btn.setCheckable(True)
        line_btn.setFixedSize(60, 30)
        line_btn.clicked.connect(lambda: self.update_chart_as_line())
        layout.addWidget(line_btn)
        
        # Store chart type buttons
        self.chart_type_buttons = {'candlestick': candlestick_btn, 'line': line_btn}
        
        controls.setLayout(layout)
        return controls
    
    def create_order_forms(self):
        """Create buy and sell order forms with coin selection."""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Buy form
        buy_form = self.create_buy_form()
        layout.addWidget(buy_form)
        
        # Sell form
        sell_form = self.create_sell_form()
        layout.addWidget(sell_form)
        
        container.setLayout(layout)
        return container
    
    def create_buy_form(self):
        """Create buy form - buy any coin with USDT."""
        form = QFrame()
        form.setObjectName("buyForm")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("BUY")
        title.setObjectName("buyTitle")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Coin selection with icons
        coin_layout = QHBoxLayout()
        coin_label = QLabel("Coin:")
        coin_label.setFont(QFont("Segoe UI", 11))
        self.buy_coin_combo = QComboBox()
        self.buy_coin_combo.setObjectName("coinCombo")
        
        # Add all coins except USDT with icons
        for currency in [c for c in Config.DEFAULT_CURRENCIES if c != 'USDT']:
            icon_path = self.get_icon_path(f"{currency.lower()}.png")
            if os.path.exists(icon_path):
                self.buy_coin_combo.addItem(QIcon(icon_path), currency)
            else:
                self.buy_coin_combo.addItem(currency)
        
        self.buy_coin_combo.currentTextChanged.connect(self.on_buy_coin_changed)
        coin_layout.addWidget(coin_label)
        coin_layout.addWidget(self.buy_coin_combo, 1)
        layout.addLayout(coin_layout)
        
        # Current price display
        self.buy_price_display = QLabel("Price: $0.00")
        self.buy_price_display.setObjectName("priceDisplay")
        self.buy_price_display.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.buy_price_display)
        
        # Amount
        amount_layout = QHBoxLayout()
        amount_label = QLabel("Amount:")
        amount_label.setFont(QFont("Segoe UI", 11))
        self.buy_amount_input = QLineEdit()
        self.buy_amount_input.setObjectName("amountInput")
        self.buy_amount_input.setPlaceholderText("0.00000000")
        self.buy_amount_input.textChanged.connect(lambda: self.calculate_buy_total())
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.buy_amount_input, 1)
        layout.addLayout(amount_layout)
        
        # Total in USDT
        total_layout = QHBoxLayout()
        total_label = QLabel("Total:")
        total_label.setFont(QFont("Segoe UI", 11))
        self.buy_total_label = QLabel("0.00 USDT")
        self.buy_total_label.setObjectName("totalValue")
        self.buy_total_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.buy_total_label, 1)
        layout.addLayout(total_layout)
        
        # Available USDT balance
        self.buy_balance_label = QLabel("Available: 0.00 USDT")
        self.buy_balance_label.setObjectName("balanceLabel")
        self.buy_balance_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.buy_balance_label)
        
        layout.addStretch()
        
        # Buy button
        self.buy_submit_btn = QPushButton(f"BUY BTC")
        self.buy_submit_btn.setObjectName("buyButton")
        self.buy_submit_btn.setMinimumHeight(45)
        self.buy_submit_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.buy_submit_btn.clicked.connect(self.execute_buy)
        layout.addWidget(self.buy_submit_btn)
        
        form.setLayout(layout)
        return form
    
    def create_sell_form(self):
        """Create sell form - sell any coin for USDT."""
        form = QFrame()
        form.setObjectName("sellForm")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("SELL")
        title.setObjectName("sellTitle")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Coin selection with icons
        coin_layout = QHBoxLayout()
        coin_label = QLabel("Coin:")
        coin_label.setFont(QFont("Segoe UI", 11))
        self.sell_coin_combo = QComboBox()
        self.sell_coin_combo.setObjectName("coinCombo")
        
        # Add all coins except USDT with icons
        for currency in [c for c in Config.DEFAULT_CURRENCIES if c != 'USDT']:
            icon_path = self.get_icon_path(f"{currency.lower()}.png")
            if os.path.exists(icon_path):
                self.sell_coin_combo.addItem(QIcon(icon_path), currency)
            else:
                self.sell_coin_combo.addItem(currency)
        
        self.sell_coin_combo.currentTextChanged.connect(self.on_sell_coin_changed)
        coin_layout.addWidget(coin_label)
        coin_layout.addWidget(self.sell_coin_combo, 1)
        layout.addLayout(coin_layout)
        
        # Current holdings card (NEW)
        holdings_card = QFrame()
        holdings_card.setObjectName("holdingsCard")
        holdings_card.setStyleSheet("""
            QFrame#holdingsCard {
                background-color: #1E2329;
                border: 1px solid #2B3139;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        holdings_layout = QVBoxLayout()
        holdings_layout.setSpacing(4)
        
        holdings_title = QLabel("Your Holdings")
        holdings_title.setFont(QFont("Segoe UI", 9))
        holdings_title.setStyleSheet("color: #848E9C;")
        holdings_layout.addWidget(holdings_title)
        
        self.sell_holdings_label = QLabel("0.00000000 BTC")
        self.sell_holdings_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.sell_holdings_label.setStyleSheet("color: #EAECEF;")
        holdings_layout.addWidget(self.sell_holdings_label)
        
        self.sell_holdings_value_label = QLabel("≈ $0.00 USDT")
        self.sell_holdings_value_label.setFont(QFont("Segoe UI", 10))
        self.sell_holdings_value_label.setStyleSheet("color: #848E9C;")
        holdings_layout.addWidget(self.sell_holdings_value_label)
        
        holdings_card.setLayout(holdings_layout)
        layout.addWidget(holdings_card)
        
        # Current price display
        self.sell_price_display = QLabel("Price: $0.00")
        self.sell_price_display.setObjectName("priceDisplay")
        self.sell_price_display.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.sell_price_display)
        
        # Amount
        amount_layout = QHBoxLayout()
        amount_label = QLabel("Amount:")
        amount_label.setFont(QFont("Segoe UI", 11))
        self.sell_amount_input = QLineEdit()
        self.sell_amount_input.setObjectName("amountInput")
        self.sell_amount_input.setPlaceholderText("0.00000000")
        self.sell_amount_input.textChanged.connect(lambda: self.calculate_sell_total())
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.sell_amount_input, 1)
        layout.addLayout(amount_layout)
        
        # Total in USDT
        total_layout = QHBoxLayout()
        total_label = QLabel("Total:")
        total_label.setFont(QFont("Segoe UI", 11))
        self.sell_total_label = QLabel("0.00 USDT")
        self.sell_total_label.setObjectName("totalValue")
        self.sell_total_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.sell_total_label, 1)
        layout.addLayout(total_layout)
        
        # Available coin balance
        self.sell_balance_label = QLabel("Available: 0.00000000 BTC")
        self.sell_balance_label.setObjectName("balanceLabel")
        self.sell_balance_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.sell_balance_label)
        
        layout.addStretch()
        
        # Sell button
        self.sell_submit_btn = QPushButton(f"SELL BTC")
        self.sell_submit_btn.setObjectName("sellButton")
        self.sell_submit_btn.setMinimumHeight(45)
        self.sell_submit_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.sell_submit_btn.clicked.connect(self.execute_sell)
        layout.addWidget(self.sell_submit_btn)
        
        form.setLayout(layout)
        return form
    
    def create_info_panel(self):
        """Create the info panel with portfolio."""
        panel = QFrame()
        panel.setObjectName("infoPanel")
        panel.setMaximumWidth(350)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Portfolio section
        portfolio_title = QLabel("Portfolio")
        portfolio_title.setObjectName("panelTitle")
        portfolio_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(portfolio_title)
        
        # Total value
        self.total_value_label = QLabel("Total: $0.00")
        self.total_value_label.setObjectName("totalValue")
        self.total_value_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(self.total_value_label)
        
        # Wallet table
        self.wallet_table = QTableWidget()
        self.wallet_table.setObjectName("walletTable")
        self.wallet_table.setColumnCount(2)
        self.wallet_table.setHorizontalHeaderLabels(['Currency', 'Balance'])
        self.wallet_table.horizontalHeader().setStretchLastSection(True)
        self.wallet_table.verticalHeader().setVisible(False)
        layout.addWidget(self.wallet_table)
        
        panel.setLayout(layout)
        return panel
    
    def create_history_table(self):
        """Create a table for order/trade history."""
        table = QTableWidget()
        table.setObjectName("historyTable")
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(['Time', 'Pair', 'Type', 'Side', 'Price', 'Amount', 'Status'])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        return table
    
    def create_p2p_trading_tab(self):
        """Create the P2P trading tab with offer creation and listing."""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Left side: Create offer (more compact)
        create_offer_panel = QFrame()
        create_offer_panel.setObjectName("p2pCreatePanel")
        create_offer_panel.setMaximumWidth(280)
        create_offer_panel.setMinimumWidth(280)
        create_layout = QVBoxLayout()
        create_layout.setContentsMargins(8, 8, 8, 8)
        create_layout.setSpacing(6)
        
        # Title
        create_title = QLabel("Create Offer")
        create_title.setObjectName("panelTitle")
        create_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        create_layout.addWidget(create_title)
        
        # Offering section (compact)
        offer_label = QLabel("Offering:")
        offer_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        create_layout.addWidget(offer_label)
        
        self.offer_currency_combo = QComboBox()
        self.offer_currency_combo.setObjectName("p2pCombo")
        
        # Add all coins with icons
        for currency in Config.DEFAULT_CURRENCIES:
            icon_path = self.get_icon_path(f"{currency.lower()}.png")
            if os.path.exists(icon_path):
                self.offer_currency_combo.addItem(QIcon(icon_path), currency)
            else:
                self.offer_currency_combo.addItem(currency)
        
        self.offer_currency_combo.currentTextChanged.connect(self.update_p2p_offer_balance)
        create_layout.addWidget(self.offer_currency_combo)
        
        # Your balance card
        self.offer_balance_card = QFrame()
        self.offer_balance_card.setStyleSheet("""
            QFrame {
                background-color: #1E2329;
                border: 1px solid #2B3139;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        balance_layout = QVBoxLayout()
        balance_layout.setSpacing(2)
        
        balance_title = QLabel("Your Balance")
        balance_title.setFont(QFont("Segoe UI", 8))
        balance_title.setStyleSheet("color: #848E9C;")
        balance_layout.addWidget(balance_title)
        
        self.offer_balance_label = QLabel("0.00000000 BTC")
        self.offer_balance_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.offer_balance_label.setStyleSheet("color: #EAECEF;")
        balance_layout.addWidget(self.offer_balance_label)
        
        self.offer_balance_card.setLayout(balance_layout)
        create_layout.addWidget(self.offer_balance_card)
        
        self.offer_amount_input = QLineEdit()
        self.offer_amount_input.setObjectName("p2pInput")
        self.offer_amount_input.setPlaceholderText("Amount")
        create_layout.addWidget(self.offer_amount_input)
        
        # Requesting section (compact)
        request_label = QLabel("Want:")
        request_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        create_layout.addWidget(request_label)
        
        self.request_currency_combo = QComboBox()
        self.request_currency_combo.setObjectName("p2pCombo")
        
        # Add all coins with icons
        for currency in Config.DEFAULT_CURRENCIES:
            icon_path = self.get_icon_path(f"{currency.lower()}.png")
            if os.path.exists(icon_path):
                self.request_currency_combo.addItem(QIcon(icon_path), currency)
            else:
                self.request_currency_combo.addItem(currency)
        
        # Find USDT index and set as default
        usdt_index = Config.DEFAULT_CURRENCIES.index('USDT') if 'USDT' in Config.DEFAULT_CURRENCIES else 0
        self.request_currency_combo.setCurrentIndex(usdt_index)
        create_layout.addWidget(self.request_currency_combo)
        
        self.request_amount_input = QLineEdit()
        self.request_amount_input.setObjectName("p2pInput")
        self.request_amount_input.setPlaceholderText("Amount")
        create_layout.addWidget(self.request_amount_input)
        
        create_layout.addStretch()
        
        # Create button
        create_offer_btn = QPushButton("Create Offer")
        create_offer_btn.setObjectName("createOfferButton")
        create_offer_btn.setMinimumHeight(32)
        create_offer_btn.clicked.connect(self.create_trade_offer)
        create_layout.addWidget(create_offer_btn)
        
        create_offer_panel.setLayout(create_layout)
        layout.addWidget(create_offer_panel)
        
        # Right side: Tabs for All Offers and My Offers
        offers_tabs = QTabWidget()
        offers_tabs.setObjectName("p2pOffersTabs")
        
        # All offers table (fixed columns)
        self.all_offers_table = QTableWidget()
        self.all_offers_table.setObjectName("p2pOffersTable")
        self.all_offers_table.setColumnCount(6)
        self.all_offers_table.setHorizontalHeaderLabels(['User', 'Offering', 'Amount', 'Wants', 'Amount', 'Action'])
        self.all_offers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.all_offers_table.verticalHeader().setVisible(False)
        self.all_offers_table.setColumnWidth(0, 120)  # User
        self.all_offers_table.setColumnWidth(1, 100)  # Offering
        self.all_offers_table.setColumnWidth(2, 150)  # Amount
        self.all_offers_table.setColumnWidth(3, 100)  # Wants
        self.all_offers_table.setColumnWidth(4, 150)  # Amount
        self.all_offers_table.setColumnWidth(5, 100)  # Action
        offers_tabs.addTab(self.all_offers_table, "Available")
        
        # My offers table (fixed columns)
        self.my_offers_table = QTableWidget()
        self.my_offers_table.setObjectName("p2pOffersTable")
        self.my_offers_table.setColumnCount(6)
        self.my_offers_table.setHorizontalHeaderLabels(['Time', 'Offering', 'Amount', 'Wants', 'Amount', 'Action'])
        self.my_offers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.my_offers_table.verticalHeader().setVisible(False)
        self.my_offers_table.setColumnWidth(0, 140)  # Time
        self.my_offers_table.setColumnWidth(1, 100)  # Offering
        self.my_offers_table.setColumnWidth(2, 150)  # Amount
        self.my_offers_table.setColumnWidth(3, 100)  # Wants
        self.my_offers_table.setColumnWidth(4, 150)  # Amount
        self.my_offers_table.setColumnWidth(5, 80)   # Action
        offers_tabs.addTab(self.my_offers_table, "My Offers")
        
        layout.addWidget(offers_tabs, 1)
        
        container.setLayout(layout)
        return container
    
    def create_trade_offer(self):
        """Create a new P2P trade offer."""
        try:
            offering_currency = self.offer_currency_combo.currentText()
            offering_amount = self.offer_amount_input.text()
            requesting_currency = self.request_currency_combo.currentText()
            requesting_amount = self.request_amount_input.text()
            
            if not offering_amount or not requesting_amount:
                styled_dialogs.show_warning(self, "Invalid Input", "Please enter both amounts.")
                return
            
            offering_amount = float(offering_amount)
            requesting_amount = float(requesting_amount)
            
            if offering_amount <= 0 or requesting_amount <= 0:
                styled_dialogs.show_warning(self, "Invalid Amount", "Amounts must be greater than 0.")
                return
            
            if offering_currency == requesting_currency:
                styled_dialogs.show_warning(self, "Invalid Trade", "You cannot trade a currency for itself.")
                return
            
            # Create the offer in database
            result = self.db.create_trade_offer(
                user_id=self.user_id,
                offering_currency=offering_currency,
                offering_amount=offering_amount,
                requesting_currency=requesting_currency,
                requesting_amount=requesting_amount
            )
            
            if result['success']:
                styled_dialogs.show_success(self, "Offer Created ✨", "Your trade offer has been created successfully!")
                self.offer_amount_input.clear()
                self.request_amount_input.clear()
                self.refresh_p2p_offers()
            else:
                styled_dialogs.show_warning(self, "Failed", result.get('error', 'Failed to create offer'))
                
        except ValueError:
            styled_dialogs.show_warning(self, "Invalid Input", "Please enter valid numbers.")
        except Exception as e:
            styled_dialogs.show_error(self, "Error", f"An error occurred: {str(e)}")
    
    def refresh_p2p_offers(self):
        """Refresh the P2P offers tables."""
        try:
            # Get all active offers
            all_offers = self.db.get_all_trade_offers(exclude_user_id=self.user_id)
            self.populate_p2p_offers_table(self.all_offers_table, all_offers, show_accept=True)
            
            # Get user's offers
            my_offers = self.db.get_user_trade_offers(self.user_id)
            self.populate_p2p_offers_table(self.my_offers_table, my_offers, show_accept=False)
            
        except Exception as e:
            print(f"Error refreshing P2P offers: {e}")
    
    def populate_p2p_offers_table(self, table, offers, show_accept=True):
        """Populate P2P offers table."""
        table.setRowCount(0)
        
        for offer in offers:
            row = table.rowCount()
            table.insertRow(row)
            
            if show_accept:
                # All offers table - show creator name
                creator_name = offer.get('creator_name', 'Unknown')[:15]
                table.setItem(row, 0, QTableWidgetItem(creator_name))
            else:
                # My offers table - show created time
                created_at = offer.get('created_at', '')
                if isinstance(created_at, str):
                    timestamp = created_at[:16]
                else:
                    # It's a datetime object
                    timestamp = created_at.strftime('%Y-%m-%d %H:%M') if created_at else ''
                table.setItem(row, 0, QTableWidgetItem(timestamp))
            
            # Offering
            table.setItem(row, 1, QTableWidgetItem(offer['offering_currency']))
            table.setItem(row, 2, QTableWidgetItem(f"{float(offer['offering_amount']):.8f}"))
            
            # Requesting
            table.setItem(row, 3, QTableWidgetItem(offer['requesting_currency']))
            table.setItem(row, 4, QTableWidgetItem(f"{float(offer['requesting_amount']):.8f}"))
            
            # Action button
            if show_accept:
                accept_btn = QPushButton("✓ Accept")
                accept_btn.setObjectName("acceptOfferButton")
                accept_btn.clicked.connect(lambda checked, offer_id=offer['offer_id']: self.accept_trade_offer(offer_id))
                table.setCellWidget(row, 5, accept_btn)
            else:
                cancel_btn = QPushButton("✕ Cancel")
                cancel_btn.setObjectName("cancelOfferButton")
                cancel_btn.clicked.connect(lambda checked, offer_id=offer['offer_id']: self.cancel_trade_offer(offer_id))
                table.setCellWidget(row, 5, cancel_btn)
    
    def accept_trade_offer(self, offer_id):
        """Accept a P2P trade offer."""
        try:
            result = self.db.accept_trade_offer(self.user_id, offer_id)
            
            if result['success']:
                styled_dialogs.show_success(
                    self,
                    "Trade Completed! 🎉",
                    f"Trade successful!\n\n"
                    f"You received: {result['received_amount']:.8f} {result['received_currency']}\n"
                    f"You sent: {result['sent_amount']:.8f} {result['sent_currency']}"
                )
                self.force_refresh_all()
            else:
                styled_dialogs.show_warning(self, "Trade Failed", result.get('error', 'Failed to complete trade'))
                
        except Exception as e:
            styled_dialogs.show_error(self, "Error", f"An error occurred: {str(e)}")
    
    def cancel_trade_offer(self, offer_id):
        """Cancel a P2P trade offer."""
        try:
            if styled_dialogs.show_question(
                self,
                "Cancel Offer",
                "Are you sure you want to cancel this trade offer?"
            ):
                result = self.db.cancel_trade_offer(offer_id, self.user_id)
                
                if result['success']:
                    styled_dialogs.show_success(self, "Offer Cancelled", "Your trade offer has been cancelled and funds have been returned.")
                    self.force_refresh_all()
                else:
                    styled_dialogs.show_warning(self, "Failed", result.get('error', 'Failed to cancel offer'))
                    
        except Exception as e:
            styled_dialogs.show_error(self, "Error", f"An error occurred: {str(e)}")
    
    def refresh_transaction_history(self):
        """Refresh the full transaction history."""
        try:
            print("🔄 Refreshing transaction history...")
            
            # Get regular transactions (buy/sell)
            transactions = self.db.get_user_transactions(self.user_id, limit=200)
            
            # Get P2P transactions
            p2p_transactions = self.db._execute('''
                SELECT 
                    pt.created_at,
                    'p2p' as type,
                    CASE 
                        WHEN pt.acceptor_id = %s THEN to_creator.offering_currency || '/' || to_creator.requesting_currency
                        ELSE to_acceptor.requesting_currency || '/' || to_acceptor.offering_currency
                    END as pair,
                    CASE 
                        WHEN pt.acceptor_id = %s THEN to_creator.offering_amount
                        ELSE to_acceptor.requesting_amount
                    END as amount,
                    CASE 
                        WHEN pt.acceptor_id = %s THEN to_creator.requesting_amount / NULLIF(to_creator.offering_amount, 0)
                        ELSE to_acceptor.offering_amount / NULLIF(to_acceptor.requesting_amount, 0)
                    END as price,
                    CASE 
                        WHEN pt.acceptor_id = %s THEN to_creator.requesting_amount
                        ELSE to_acceptor.offering_amount
                    END as total,
                    0.0 as fee
                FROM "P2PTradeTransactions" pt
                JOIN "TradeOffers" to_creator ON pt.offer_id = to_creator.offer_id
                JOIN "TradeOffers" to_acceptor ON pt.offer_id = to_acceptor.offer_id
                WHERE pt.acceptor_id = %s OR to_creator.creator_id = %s
                ORDER BY pt.created_at DESC
                LIMIT 100
            ''', (self.user_id, self.user_id, self.user_id, self.user_id, self.user_id, self.user_id))
            
            # Combine and sort all transactions
            all_transactions = []
            
            for tx in transactions:
                all_transactions.append({
                    'created_at': tx.get('created_at'),
                    'type': tx.get('type'),
                    'pair': tx.get('pair'),
                    'amount': float(tx.get('amount', 0)),
                    'price': float(tx.get('price', 0)),
                    'fee': float(tx.get('fee', 0))
                })
            
            for tx in p2p_transactions:
                all_transactions.append({
                    'created_at': tx.get('created_at'),
                    'type': 'p2p',
                    'pair': tx.get('pair'),
                    'amount': float(tx.get('amount', 0)),
                    'price': float(tx.get('price', 0)),
                    'fee': float(tx.get('fee', 0))
                })
            
            # Sort by date (newest first)
            all_transactions.sort(key=lambda x: x['created_at'] if x['created_at'] else '', reverse=True)
            
            # Store for filtering
            self.all_transactions = all_transactions
            
            # Apply current filter
            self.filter_history(self.current_history_filter)
            
            print(f"✅ Loaded {len(all_transactions)} transactions")
            
        except Exception as e:
            print(f"Error refreshing transaction history: {e}")
            import traceback
            traceback.print_exc()
    
    def filter_history(self, filter_type):
        """Filter transaction history by type."""
        self.current_history_filter = filter_type
        
        if not hasattr(self, 'all_transactions'):
            return
        
        # Filter transactions
        if filter_type == "all":
            filtered = self.all_transactions
        else:
            filtered = [tx for tx in self.all_transactions if tx['type'] == filter_type]
        
        # Populate table
        self.populate_full_history_table(filtered)
    
    def populate_full_history_table(self, transactions):
        """Populate the full transaction history table."""
        self.history_full_table.setRowCount(0)
        
        for tx in transactions:
            row = self.history_full_table.rowCount()
            self.history_full_table.insertRow(row)
            
            # Time
            created_at = tx.get('created_at', '')
            if isinstance(created_at, str):
                timestamp = created_at[:19]
            else:
                timestamp = created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else ''
            self.history_full_table.setItem(row, 0, QTableWidgetItem(timestamp))
            
            # Type
            tx_type = tx.get('type', '').upper()
            type_item = QTableWidgetItem(tx_type)
            type_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            
            # Color code by type
            if tx_type == 'BUY':
                type_item.setForeground(QColor("#0ECB81"))  # Green
            elif tx_type == 'SELL':
                type_item.setForeground(QColor("#F6465D"))  # Red
            else:
                type_item.setForeground(QColor("#FCD535"))  # Yellow for P2P
            
            self.history_full_table.setItem(row, 1, type_item)
            
            # Pair
            self.history_full_table.setItem(row, 2, QTableWidgetItem(tx.get('pair', '')))
            
            # Amount
            amount_item = QTableWidgetItem(f"{tx.get('amount', 0):.8f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.history_full_table.setItem(row, 3, amount_item)
            
            # Price
            price_item = QTableWidgetItem(f"${tx.get('price', 0):,.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.history_full_table.setItem(row, 4, price_item)
            
            # Total
            total = tx.get('amount', 0) * tx.get('price', 0)
            total_item = QTableWidgetItem(f"${total:,.2f}")
            total_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.history_full_table.setItem(row, 5, total_item)
            
            # Fee
            fee_item = QTableWidgetItem(f"${tx.get('fee', 0):.2f}")
            fee_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.history_full_table.setItem(row, 6, fee_item)
    
    def add_market_row(self, pair):
        """Add a row to the market table with coin icon."""
        row = self.market_table.rowCount()
        self.market_table.insertRow(row)
        
        # Extract base symbol from pair (e.g., "BTC/USDT" -> "BTC")
        base_symbol = pair.split('/')[0]
        
        # Create pair item with icon
        pair_item = QTableWidgetItem(pair)
        pair_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        
        # Try to load coin icon
        icon_path = f"assets/icons/{base_symbol.lower()}.png"
        if os.path.exists(icon_path):
            pair_item.setIcon(QIcon(icon_path))
        
        self.market_table.setItem(row, 0, pair_item)
        
        # Price
        price_item = QTableWidgetItem("$0.00")
        price_item.setFont(QFont("Segoe UI", 12))
        price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.market_table.setItem(row, 1, price_item)
        
        # 24h Change
        change_item = QTableWidgetItem("0.00%")
        change_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        change_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.market_table.setItem(row, 2, change_item)
        
        # Set row height for better spacing
        self.market_table.setRowHeight(row, 48)
    
    def load_initial_data(self):
        """Load initial data (wallets, orders, etc.)."""
        try:
            print("[INIT] Loading wallet display...")
            self.update_wallet_display()
            print("[INIT] Loading order history...")
            self.update_order_history()
            print("[INIT] Loading chart...")
            self.update_chart()  # Load initial chart
            
            # Initialize buy and sell forms
            print("[INIT] Initializing buy form...")
            self.on_buy_coin_changed()
            print("[INIT] Initializing sell form...")
            self.on_sell_coin_changed()
            
            # Initialize P2P balance display and load offers
            print("[INIT] Initializing P2P balance...")
            self.update_p2p_offer_balance()
            print("[INIT] Loading P2P offers...")
            self.refresh_p2p_offers()
            print("[INIT] Loading transaction history...")
            self.refresh_transaction_history()
            print("[INIT] ✅ Initial data loaded successfully!")
        except Exception as e:
            print(f"[INIT] ⚠️ Error during initialization: {e}")
            import traceback
            traceback.print_exc()
    
    def update_prices(self):
        """Update all cryptocurrency prices."""
        try:
            # Get all unique symbols
            symbols = set()
            for pair in Config.DEFAULT_TRADING_PAIRS:
                base, quote = pair.split('/')
                symbols.add(base)
                symbols.add(quote)
            
            # Fetch prices (returns {'BTC': 98000, 'ETH': 3500, ...})
            prices = self.price_service.get_multiple_prices(list(symbols))
            
            # Check if we got any prices
            if not prices or len(prices) == 0:
                print("⚠️ Warning: No prices received from API")
                # Show warning in price display
                if hasattr(self, 'price_value'):
                    self.price_value.setText("API Error")
                    self.price_label_title.setText("⚠️ Price API Unavailable")
                return
            
            # Convert to pair format for wallet display
            # {'BTC': 98000} -> {'BTC/USDT': 98000}
            self.current_prices = {}
            for symbol, price in prices.items():
                if symbol != 'USDT' and price:
                    self.current_prices[f"{symbol}/USDT"] = price
            
            # Update market table
            for row in range(self.market_table.rowCount()):
                pair = self.market_table.item(row, 0).text()
                price = self.price_service.get_pair_price(pair)
                
                if price:
                    # Update price
                    price_item = QTableWidgetItem(f"${price:,.2f}")
                    price_item.setFont(QFont("Segoe UI", 12))
                    price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.market_table.setItem(row, 1, price_item)
                    
                    # Get real 24h change from price service
                    change_data = self.price_service.get_24h_change(pair.split('/')[0])
                    if change_data:
                        change = change_data.get('price_change_percentage_24h', 0)
                    else:
                        change = 0
                    
                    change_item = QTableWidgetItem(f"{change:+.2f}%")
                    change_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                    change_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
                    # Color code the change
                    if change >= 0:
                        change_item.setForeground(QColor("#0ECB81"))
                    else:
                        change_item.setForeground(QColor("#F6465D"))
                    
                    self.market_table.setItem(row, 2, change_item)
            
            # Cycle through coins for price display
            if self.price_display_pairs:
                display_pair = self.price_display_pairs[self.price_display_index]
                display_price = self.price_service.get_pair_price(display_pair)
                
                if display_price:
                    self.price_label_title.setText(display_pair)
                    self.price_value.setText(f"${display_price:,.2f}")
                
                # Move to next coin for next update
                self.price_display_index = (self.price_display_index + 1) % len(self.price_display_pairs)
            
            # Update header with current trading pair
            current_price = self.price_service.get_pair_price(self.current_pair)
            if current_price:
                self.header_price_label.setText(f"${current_price:,.2f}")
                self.calculate_total("BUY")
                self.calculate_total("SELL")
            
            # Update portfolio value and wallet display
            self.update_portfolio_value()
            self.update_wallet_display()
            
        except Exception as e:
            print(f"❌ Error updating prices: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error in UI
            if hasattr(self, 'price_value'):
                self.price_value.setText("Connection Error")
                self.price_label_title.setText("⚠️ Check Internet Connection")
    
    def update_chart(self):
        """Update the chart with current pair."""
        try:
            # Extract base symbol from pair (e.g., "BTC/USDT" -> "BTC")
            base_symbol = self.current_pair.split('/')[0]
            
            # Load CoinGecko chart for the symbol
            self.chart_widget.load_chart(base_symbol)
                
        except Exception as e:
            print(f"Error updating chart: {e}")
            self.chart_widget.plot_empty("Failed to load chart data")
    
    def update_wallet_display(self):
        """Update the wallet display."""
        try:
            wallets = self.db.get_user_wallets(self.user_id)
            
            print(f"[DEBUG] Updating wallet display - Found {len(wallets)} wallets")
            print(f"[DEBUG] Current prices available: {list(self.current_prices.keys())[:5]}...")
            
            self.wallet_table.setRowCount(0)
            
            for wallet in wallets:
                row = self.wallet_table.rowCount()
                self.wallet_table.insertRow(row)
                
                currency = wallet['currency']
                balance = float(wallet['balance'])
                
                # Currency column with icon
                currency_item = QTableWidgetItem(currency)
                currency_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                icon_path = self.get_icon_path(f"{currency.lower()}.png")
                if os.path.exists(icon_path):
                    currency_item.setIcon(QIcon(icon_path))
                self.wallet_table.setItem(row, 0, currency_item)
                
                # Balance column
                balance_item = QTableWidgetItem(f"{balance:.8f}")
                self.wallet_table.setItem(row, 1, balance_item)
                
                # Value in USDT column (if exists)
                if self.wallet_table.columnCount() == 3:
                    value_usdt = 0.0
                    if currency == 'USDT':
                        value_usdt = balance
                    elif f"{currency}/USDT" in self.current_prices:
                        price = self.current_prices[f"{currency}/USDT"]
                        value_usdt = balance * price
                        print(f"[DEBUG] {currency}: {balance} * ${price} = ${value_usdt}")
                    else:
                        print(f"[DEBUG] No price found for {currency}/USDT")
                    
                    value_item = QTableWidgetItem(f"${value_usdt:.2f}")
                    if value_usdt > 0:
                        value_item.setForeground(QColor("#0ECB81"))
                    self.wallet_table.setItem(row, 2, value_item)
            
            # Update balance labels in order forms
            self.update_balance_labels()
            
        except Exception as e:
            print(f"Error updating wallet: {e}")
            import traceback
            traceback.print_exc()
    
    def update_balance_labels(self):
        """Update available balance labels in order forms."""
        try:
            base, quote = self.current_pair.split('/')
            
            # Buy form shows quote currency balance (e.g., USDT)
            quote_wallet = self.db.get_wallet_balance(self.user_id, quote)
            if quote_wallet:
                self.buy_balance_label.setText(f"Available: {float(quote_wallet['balance']):.2f} {quote}")
            
            # Sell form shows base currency balance (e.g., BTC)
            base_wallet = self.db.get_wallet_balance(self.user_id, base)
            if base_wallet:
                self.sell_balance_label.setText(f"Available: {float(base_wallet['balance']):.8f} {base}")
                
        except Exception as e:
            print(f"Error updating balance labels: {e}")
    
    def update_portfolio_value(self):
        """Calculate and display total portfolio value with P&L."""
        try:
            from datetime import datetime, timedelta
            
            portfolio = self.db.get_portfolio_value(self.user_id, self.current_prices)
            total_value = portfolio['total_value']
            
            self.total_value_label.setText(f"${total_value:,.2f}")
            
            # Calculate total P&L (vs initial $10,000)
            initial_balance = 10000.0
            total_pnl = total_value - initial_balance
            total_pnl_percent = (total_pnl / initial_balance) * 100
            
            # Update total P&L
            self.total_pnl_label.setText(f"${total_pnl:+,.2f}")
            self.total_pnl_percent.setText(f"({total_pnl_percent:+.2f}%)")
            
            # Color code total P&L
            if total_pnl > 0:
                self.total_pnl_label.setStyleSheet("color: #0ECB81;")  # Green
                self.total_pnl_percent.setStyleSheet("color: #0ECB81;")
            elif total_pnl < 0:
                self.total_pnl_label.setStyleSheet("color: #F6465D;")  # Red
                self.total_pnl_percent.setStyleSheet("color: #F6465D;")
            else:
                self.total_pnl_label.setStyleSheet("color: #EAECEF;")  # White
                self.total_pnl_percent.setStyleSheet("color: #848E9C;")  # Gray
            
            # Calculate today's P&L (based on transactions from today)
            from datetime import timezone
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            transactions = self.db.get_user_transactions(self.user_id, limit=1000)
            
            # Calculate portfolio value at start of today
            today_transactions = []
            for tx in transactions:
                tx_time = tx.get('created_at')
                if isinstance(tx_time, str):
                    from dateutil import parser
                    tx_time = parser.parse(tx_time)
                
                # Make both timezone-aware for comparison
                if tx_time.tzinfo is None:
                    tx_time = tx_time.replace(tzinfo=timezone.utc)
                
                if tx_time >= today_start:
                    today_transactions.append(tx)
            
            # Calculate value change from today's transactions
            today_pnl = 0.0
            for tx in today_transactions:
                tx_type = tx.get('type', '').lower()
                pair = tx.get('pair', '')
                amount = float(tx.get('amount', 0))
                price = float(tx.get('price', 0))
                fee = float(tx.get('fee', 0))
                
                if tx_type == 'buy':
                    # Money spent (negative)
                    today_pnl -= (amount * price + fee)
                    # Current value of bought coins (positive)
                    current_price = self.current_prices.get(pair, price)
                    today_pnl += (amount * current_price)
                elif tx_type == 'sell':
                    # Money received (positive)
                    today_pnl += (amount * price - fee)
                    # Value of sold coins at current price (negative - what we lost)
                    current_price = self.current_prices.get(pair, price)
                    today_pnl -= (amount * current_price)
            
            # Update today's P&L
            if len(today_transactions) > 0:
                self.today_pnl_label.setText(f"${today_pnl:+,.2f}")
                today_base = total_value - today_pnl if (total_value - today_pnl) > 0 else initial_balance
                today_pnl_percent = (today_pnl / today_base) * 100 if today_base > 0 else 0
                self.today_pnl_percent.setText(f"({today_pnl_percent:+.2f}%)")
                
                # Color code today's P&L
                if today_pnl > 0:
                    self.today_pnl_label.setStyleSheet("color: #0ECB81;")  # Green
                    self.today_pnl_percent.setStyleSheet("color: #0ECB81;")
                elif today_pnl < 0:
                    self.today_pnl_label.setStyleSheet("color: #F6465D;")  # Red
                    self.today_pnl_percent.setStyleSheet("color: #F6465D;")
                else:
                    self.today_pnl_label.setStyleSheet("color: #EAECEF;")
                    self.today_pnl_percent.setStyleSheet("color: #848E9C;")
            else:
                self.today_pnl_label.setText("$0.00")
                self.today_pnl_percent.setText("(No trades today)")
                self.today_pnl_label.setStyleSheet("color: #848E9C;")
                self.today_pnl_percent.setStyleSheet("color: #848E9C;")
            
            # Update profit breakdown by coin
            self.update_profit_breakdown()
            
        except Exception as e:
            print(f"Error updating portfolio value: {e}")
            import traceback
            traceback.print_exc()
    
    def update_profit_breakdown(self):
        """Update the profit breakdown table showing P&L for each coin."""
        try:
            # Get all transactions to calculate cost basis
            transactions = self.db.get_user_transactions(self.user_id, limit=1000)
            
            # Calculate cost basis for each coin
            coin_data = {}  # {currency: {'total_bought': amount, 'total_cost': usd, 'total_sold': amount, 'total_revenue': usd}}
            
            for tx in transactions:
                tx_type = tx.get('type', '').lower()
                pair = tx.get('pair', '')
                amount = float(tx.get('amount', 0))
                price = float(tx.get('price', 0))
                fee = float(tx.get('fee', 0))
                
                if '/' not in pair:
                    continue
                    
                base_currency, quote_currency = pair.split('/')
                
                if tx_type == 'buy':
                    # Buying base currency with quote currency
                    if base_currency not in coin_data:
                        coin_data[base_currency] = {'total_bought': 0, 'total_cost': 0, 'total_sold': 0, 'total_revenue': 0}
                    coin_data[base_currency]['total_bought'] += amount
                    coin_data[base_currency]['total_cost'] += (amount * price + fee)
                    
                elif tx_type == 'sell':
                    # Selling base currency for quote currency
                    if base_currency not in coin_data:
                        coin_data[base_currency] = {'total_bought': 0, 'total_cost': 0, 'total_sold': 0, 'total_revenue': 0}
                    coin_data[base_currency]['total_sold'] += amount
                    coin_data[base_currency]['total_revenue'] += (amount * price - fee)
            
            # Get current wallet balances
            wallets = self.db.get_all_wallets(self.user_id)
            
            # Clear and populate table
            self.profit_breakdown_table.setRowCount(0)
            
            for wallet in wallets:
                currency = wallet['currency']
                balance = float(wallet['balance'])
                
                # Skip if balance is 0 and no trading history
                if balance == 0 and currency not in coin_data:
                    continue
                
                row = self.profit_breakdown_table.rowCount()
                self.profit_breakdown_table.insertRow(row)
                
                # Coin name with icon
                coin_item = QTableWidgetItem(currency)
                coin_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                icon_path = self.get_icon_path(f"{currency.lower()}.png")
                if os.path.exists(icon_path):
                    coin_item.setIcon(QIcon(icon_path))
                self.profit_breakdown_table.setItem(row, 0, coin_item)
                
                # Holdings
                holdings_item = QTableWidgetItem(f"{balance:.8f}")
                holdings_item.setFont(QFont("Segoe UI", 10))
                self.profit_breakdown_table.setItem(row, 1, holdings_item)
                
                # Current value
                if currency == 'USDT':
                    current_value = balance
                else:
                    pair = f"{currency}/USDT"
                    current_price = self.current_prices.get(pair, 0)
                    current_value = balance * current_price
                
                value_item = QTableWidgetItem(f"${current_value:,.2f}")
                value_item.setFont(QFont("Segoe UI", 10))
                value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.profit_breakdown_table.setItem(row, 2, value_item)
                
                # Cost basis and P&L
                if currency in coin_data:
                    data = coin_data[currency]
                    total_bought = data['total_bought']
                    total_cost = data['total_cost']
                    total_sold = data['total_sold']
                    total_revenue = data['total_revenue']
                    
                    # Remaining coins after sells
                    remaining = total_bought - total_sold
                    
                    # Average cost per coin for remaining holdings
                    if remaining > 0 and total_bought > 0:
                        avg_cost_per_coin = total_cost / total_bought
                        cost_basis = remaining * avg_cost_per_coin
                    else:
                        cost_basis = 0
                    
                    # Realized P&L from sells
                    realized_pnl = total_revenue - (total_sold * (total_cost / total_bought if total_bought > 0 else 0))
                    
                    # Unrealized P&L from current holdings
                    unrealized_pnl = current_value - cost_basis
                    
                    # Total P&L = realized + unrealized
                    total_coin_pnl = realized_pnl + unrealized_pnl
                    
                else:
                    # No trading history (probably USDT from initial balance)
                    cost_basis = current_value
                    total_coin_pnl = 0
                
                # Cost basis
                cost_item = QTableWidgetItem(f"${cost_basis:,.2f}")
                cost_item.setFont(QFont("Segoe UI", 10))
                cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.profit_breakdown_table.setItem(row, 3, cost_item)
                
                # P&L with color coding
                pnl_text = f"${total_coin_pnl:+,.2f}"
                pnl_item = QTableWidgetItem(pnl_text)
                pnl_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                if total_coin_pnl > 0:
                    pnl_item.setForeground(QColor("#0ECB81"))  # Green
                elif total_coin_pnl < 0:
                    pnl_item.setForeground(QColor("#F6465D"))  # Red
                else:
                    pnl_item.setForeground(QColor("#848E9C"))  # Gray
                
                self.profit_breakdown_table.setItem(row, 4, pnl_item)
        
        except Exception as e:
            print(f"Error updating profit breakdown: {e}")
            import traceback
            traceback.print_exc()
    
    def update_order_history(self):
        """Update order history tables."""
        try:
            # Get transactions
            transactions = self.db.get_user_transactions(self.user_id, limit=50)
            self.populate_transaction_table(self.trade_history_table, transactions)
            
            # Update P2P offers
            self.refresh_p2p_offers()
            
        except Exception as e:
            print(f"Error updating order history: {e}")
    
    def populate_history_table(self, table, orders):
        """Populate a history table with orders."""
        table.setRowCount(0)
        
        for order in orders:
            row = table.rowCount()
            table.insertRow(row)
            
            # Parse timestamp
            timestamp = order.get('timestamp', '')[:19] if order.get('timestamp') else ''
            
            table.setItem(row, 0, QTableWidgetItem(timestamp))
            table.setItem(row, 1, QTableWidgetItem(order.get('pair', '')))
            table.setItem(row, 2, QTableWidgetItem(order.get('type', '')))
            table.setItem(row, 3, QTableWidgetItem(order.get('side', '')))
            table.setItem(row, 4, QTableWidgetItem(f"${float(order.get('price', 0)):,.2f}"))
            table.setItem(row, 5, QTableWidgetItem(f"{float(order.get('amount', 0)):.8f}"))
            table.setItem(row, 6, QTableWidgetItem(order.get('status', '')))
    
    def populate_transaction_table(self, table, transactions):
        """Populate a history table with transactions."""
        table.setRowCount(0)
        
        for tx in transactions:
            row = table.rowCount()
            table.insertRow(row)
            
            timestamp = tx.get('timestamp', '')[:19] if tx.get('timestamp') else ''
            
            table.setItem(row, 0, QTableWidgetItem(timestamp))
            table.setItem(row, 1, QTableWidgetItem(tx.get('pair', '')))
            table.setItem(row, 2, QTableWidgetItem('market'))
            table.setItem(row, 3, QTableWidgetItem(tx.get('type', '')))
            table.setItem(row, 4, QTableWidgetItem(f"${float(tx.get('price', 0)):,.2f}"))
            table.setItem(row, 5, QTableWidgetItem(f"{float(tx.get('amount', 0)):.8f}"))
            table.setItem(row, 6, QTableWidgetItem('filled'))
    
    def calculate_buy_total(self):
        """Calculate total USDT needed for buy order."""
        try:
            amount_text = self.buy_amount_input.text()
            if not amount_text:
                self.buy_total_label.setText("0.00 USDT")
                return
            
            amount = float(amount_text)
            coin = self.buy_coin_combo.currentText()
            pair = f"{coin}/USDT"
            
            price = self.price_service.get_pair_price(pair) or 0
            total = amount * price
            
            self.buy_total_label.setText(f"{total:.2f} USDT")
                
        except ValueError:
            self.buy_total_label.setText("0.00 USDT")
    
    def calculate_sell_total(self):
        """Calculate total USDT received from sell order."""
        try:
            amount_text = self.sell_amount_input.text()
            if not amount_text:
                self.sell_total_label.setText("0.00 USDT")
                return
            
            amount = float(amount_text)
            coin = self.sell_coin_combo.currentText()
            pair = f"{coin}/USDT"
            
            price = self.price_service.get_pair_price(pair) or 0
            total = amount * price
            
            self.sell_total_label.setText(f"{total:.2f} USDT")
                
        except ValueError:
            self.sell_total_label.setText("0.00 USDT")
    
    def on_buy_coin_changed(self):
        """Handle buy coin selection change."""
        coin = self.buy_coin_combo.currentText()
        pair = f"{coin}/USDT"
        
        # Update button text
        self.buy_submit_btn.setText(f"BUY {coin}")
        
        # Update price display
        price = self.price_service.get_pair_price(pair) or 0
        self.buy_price_display.setText(f"Price: ${price:,.8f}")
        
        # Update USDT balance
        usdt_wallet = self.db.get_wallet_balance(self.user_id, 'USDT')
        if usdt_wallet:
            self.buy_balance_label.setText(f"Available: {float(usdt_wallet['balance']):.2f} USDT")
        
        # Recalculate total
        self.calculate_buy_total()
    
    def on_sell_coin_changed(self):
        """Handle sell coin selection change."""
        coin = self.sell_coin_combo.currentText()
        pair = f"{coin}/USDT"
        
        # Update button text
        self.sell_submit_btn.setText(f"SELL {coin}")
        
        # Update price display
        price = self.price_service.get_pair_price(pair) or 0
        self.sell_price_display.setText(f"Price: ${price:,.8f}")
        
        # Update coin balance (old label - keep for compatibility)
        coin_wallet = self.db.get_wallet_balance(self.user_id, coin)
        coin_balance = 0.0
        if coin_wallet:
            coin_balance = float(coin_wallet['balance'])
            self.sell_balance_label.setText(f"Available: {coin_balance:.8f} {coin}")
        
        # Update holdings card (NEW)
        self.sell_holdings_label.setText(f"{coin_balance:.8f} {coin}")
        
        # Calculate and show value in USDT
        value_usdt = coin_balance * price if price else 0
        self.sell_holdings_value_label.setText(f"≈ ${value_usdt:,.2f} USDT")
        
        # Recalculate total
        self.calculate_sell_total()
    
    def update_p2p_offer_balance(self):
        """Update the balance display in P2P offer creation when currency selection changes."""
        coin = self.offer_currency_combo.currentText()
        
        # Get coin balance
        coin_wallet = self.db.get_wallet_balance(self.user_id, coin)
        coin_balance = 0.0
        if coin_wallet:
            coin_balance = float(coin_wallet['balance'])
        
        # Update balance display
        self.offer_balance_label.setText(f"{coin_balance:.8f} {coin}")
    
    def execute_buy(self):
        """Execute a buy order (buy coin with USDT)."""
        try:
            amount_text = self.buy_amount_input.text()
            if not amount_text:
                styled_dialogs.show_warning(self, "Invalid Input", "Please enter an amount.")
                return
            
            amount = float(amount_text)
            if amount <= 0:
                styled_dialogs.show_warning(self, "Invalid Amount", "Amount must be greater than 0.")
                return
            
            coin = self.buy_coin_combo.currentText()
            pair = f"{coin}/USDT"
            
            # Get current price
            current_price = self.price_service.get_pair_price(pair)
            if not current_price:
                styled_dialogs.show_warning(self, "Price Error", "Unable to fetch current price. Please try again.")
                return
            
            # Execute market order
            result = self.db.execute_market_order(
                user_id=self.user_id,
                pair=pair,
                side='buy',
                amount=amount,
                current_price=current_price
            )
            
            if result['success']:
                styled_dialogs.show_success(
                    self, 
                    "Order Executed ✅",
                    f"Successfully bought {coin}!\n\n"
                    f"Amount: {amount:.8f} {coin}\n"
                    f"Price: ${current_price:,.2f}\n"
                    f"Total: ${amount * current_price:.2f} USDT\n"
                    f"Fee: ${result['fee']:.2f}"
                )
                
                # Clear input
                self.buy_amount_input.clear()
                
                # Force refresh all displays
                self.force_refresh_all()
            else:
                styled_dialogs.show_warning(
                    self,
                    "Order Failed",
                    f"Order execution failed:\n{result.get('error', 'Unknown error')}"
                )
                
        except ValueError:
            styled_dialogs.show_warning(self, "Invalid Input", "Please enter a valid number.")
        except Exception as e:
            styled_dialogs.show_error(self, "Error", f"An error occurred: {str(e)}")
    
    def execute_sell(self):
        """Execute a sell order (sell coin for USDT)."""
        try:
            amount_text = self.sell_amount_input.text()
            if not amount_text:
                styled_dialogs.show_warning(self, "Invalid Input", "Please enter an amount.")
                return
            
            amount = float(amount_text)
            if amount <= 0:
                styled_dialogs.show_warning(self, "Invalid Amount", "Amount must be greater than 0.")
                return
            
            coin = self.sell_coin_combo.currentText()
            pair = f"{coin}/USDT"
            
            # Get current price
            current_price = self.price_service.get_pair_price(pair)
            if not current_price:
                styled_dialogs.show_warning(self, "Price Error", "Unable to fetch current price. Please try again.")
                return
            
            # Execute market order
            result = self.db.execute_market_order(
                user_id=self.user_id,
                pair=pair,
                side='sell',
                amount=amount,
                current_price=current_price
            )
            
            if result['success']:
                styled_dialogs.show_success(
                    self,
                    "Order Executed ✅",
                    f"Successfully sold {coin}!\n\n"
                    f"Amount: {amount:.8f} {coin}\n"
                    f"Price: ${current_price:,.2f}\n"
                    f"Total: ${amount * current_price:.2f} USDT\n"
                    f"Fee: ${result['fee']:.2f}"
                )                # Clear input
                self.sell_amount_input.clear()
                
                # Force refresh all displays
                self.force_refresh_all()
            else:
                styled_dialogs.show_warning(
                    self,
                    "Order Failed",
                    f"Order execution failed:\n{result.get('error', 'Unknown error')}"
                )
                
        except ValueError:
            styled_dialogs.show_warning(self, "Invalid Input", "Please enter a valid number.")
        except Exception as e:
            styled_dialogs.show_error(self, "Error", f"An error occurred: {str(e)}")
    
    def force_refresh_all(self):
        """Force refresh all displays after trading."""
        print("🔄 Refreshing all displays...")
        try:
            # Update wallet and balances
            self.update_wallet_display()
            
            # Update portfolio value and profit breakdown
            self.update_portfolio_value()
            
            # Update order history
            self.update_order_history()
            
            # Update form balances
            self.on_buy_coin_changed()
            self.on_sell_coin_changed()
            
            # Update P2P balance
            self.update_p2p_offer_balance()
            
            # Refresh P2P offers
            self.refresh_p2p_offers()
            
            # Refresh transaction history
            self.refresh_transaction_history()
            
            print("✅ All displays refreshed!")
        except Exception as e:
            print(f"⚠️ Error during refresh: {e}")
            import traceback
            traceback.print_exc()
    
    def calculate_total(self, side):
        """Legacy method - redirects to new methods."""
        if side == "BUY":
            self.calculate_buy_total()
        else:
            self.calculate_sell_total()
    
    def execute_order(self, side):
        """Legacy method - redirects to new methods."""
        if side == "BUY":
            self.execute_buy()
        else:
            self.execute_sell()
    
    def on_pair_selected(self, row, col):
        """Handle market pair selection."""
        pair = self.market_table.item(row, 0).text()
        self.current_pair = pair
        self.header_pair_label.setText(pair)
        
        # Update chart for new pair
        self.update_chart()
    
    def logout(self):
        """Handle logout."""
        from auth.google_auth import GoogleAuthManager
        
        if styled_dialogs.show_question(
            self,
            "Logout",
            "Are you sure you want to logout?"
        ):
            auth = GoogleAuthManager()
            auth.logout()
            
            # Close this window and show login
            self.close()
            
            from ui.login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
    
    def claim_daily_bonus(self):
        """Claim daily login bonus."""
        try:
            result = self.db.claim_daily_bonus(self.user_id)
            
            if result['success']:
                styled_dialogs.show_success(
                    self,
                    "Daily Bonus Claimed! 🎉",
                    result['message']
                )
                # Refresh wallet display
                self.update_wallet_display()
            else:
                styled_dialogs.show_info(
                    self,
                    "Daily Bonus",
                    result['message']
                )
        except Exception as e:
            styled_dialogs.show_error(self, "Error", f"Failed to claim bonus: {e}")
    
    def show_leaderboard(self):
        """Show leaderboard window."""
        try:
            from ui.leaderboard_window import LeaderboardWindow
            self.leaderboard_window = LeaderboardWindow(self.user_id)
            self.leaderboard_window.show()
        except Exception as e:
            styled_dialogs.show_error(self, "Error", f"Failed to open leaderboard: {e}")
    
    def get_icon_path(self, icon_name):
        """Get the absolute path to an icon file."""
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(current_dir, 'assets', 'icons', icon_name)
        return os.path.abspath(icon_path)
    
    def get_stylesheet(self):
        """Return Binance-style dark theme stylesheet matching official design."""
        return """
            /* Main Window - Dark Background */
            QMainWindow {
                background-color: #0B0E11;
            }
            
            /* Header - Top Navigation Bar */
            #header {
                background-color: #181A20;
                border-bottom: 1px solid #2B3139;
            }
            
            #logo {
                color: #F0B90B;
                font-weight: 700;
            }
            
            #navButton {
                background-color: transparent;
                color: #848E9C;
                border: none;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 500;
            }
            
            #navButton:hover {
                color: #EAECEF;
            }
            
            #headerPairLabel {
                color: #EAECEF;
                font-weight: 600;
            }
            
            #headerPriceLabel {
                color: #0ECB81;
                font-weight: 700;
            }
            
            #currentPair {
                color: #EAECEF;
                font-weight: 600;
            }
            
            #userLabel {
                color: #848E9C;
                font-size: 11px;
            }
            
            #depositButton {
                background-color: #F0B90B;
                color: #181A20;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            
            #depositButton:hover {
                background-color: #F8D12F;
            }
            
            #bonusButton {
                background-color: #0ECB81;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            
            #bonusButton:hover {
                background-color: #2EE5A0;
            }
            
            #leaderboardButton {
                background-color: #2B3139;
                color: #F0B90B;
                border: 1px solid #F0B90B;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            
            #leaderboardButton:hover {
                background-color: #F0B90B;
                color: #181A20;
            }
            
            #logoutButton {
                background-color: #2B3139;
                color: #EAECEF;
                border: 1px solid #2B3139;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }
            
            #logoutButton:hover {
                background-color: #F0B90B;
                color: #181A20;
                border: 1px solid #F0B90B;
            }
            
            /* Main Tabs - Market, Trading, P2P */
            #mainTabs {
                background-color: #0B0E11;
                border: none;
            }
            
            #mainTabs::pane {
                background-color: #0B0E11;
                border: none;
                border-top: 1px solid #2B3139;
            }
            
            #mainTabs::tab-bar {
                background-color: #181A20;
                border-bottom: 1px solid #2B3139;
            }
            
            #mainTabs QTabBar::tab {
                background-color: #181A20;
                color: #848E9C;
                border: none;
                border-bottom: 2px solid transparent;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 600;
                min-width: 120px;
            }
            
            #mainTabs QTabBar::tab:hover {
                color: #EAECEF;
                background-color: #1E2329;
            }
            
            #mainTabs QTabBar::tab:selected {
                color: #F0B90B;
                border-bottom: 2px solid #F0B90B;
                background-color: #0B0E11;
            }
            
            /* Side Panels - Market List & Portfolio */
            #marketPanel, #infoPanel {
                background-color: #181A20;
                border: none;
                border-right: 1px solid #2B3139;
            }
            
            /* Chart Panel */
            #chartPanel {
                background-color: #0B0E11;
                border: none;
            }
            
            /* Trading Panel - Center Chart Area */
            #tradingPanel {
                background-color: #0B0E11;
                border: none;
            }
            
            /* History Panel - Bottom Orders */
            #historyPanel {
                background-color: #181A20;
                border-top: 1px solid #2B3139;
            }
            
            #panelTitle {
                color: #EAECEF;
                padding: 8px 0px;
                font-weight: 600;
            }
            
            /* Price Display at Top of Chart */
            #priceDisplay {
                background-color: transparent;
                border: none;
                padding: 10px 0px;
            }
            
            #priceLabel {
                color: #707A8A;
                font-size: 11px;
                font-weight: 500;
            }
            
            #priceValue {
                color: #EAECEF;
                font-size: 20px;
                font-weight: 600;
            }
            
            #changeValue {
                color: #0ECB81;
                font-size: 13px;
                font-weight: 600;
            }
            
            /* Chart Controls - Time Interval Buttons */
            #chartControls {
                background-color: transparent;
                border: none;
                padding: 5px 0px;
            }
            
            #intervalLabel {
                color: #707A8A;
                font-size: 12px;
                padding: 0px 8px;
                font-weight: 500;
            }
            
            #intervalButton {
                background-color: transparent;
                color: #707A8A;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
                min-width: 32px;
            }
            
            #intervalButton:hover {
                background-color: #2B3139;
                color: #EAECEF;
            }
            
            #intervalButton:checked {
                background-color: transparent;
                color: #F0B90B;
                border: none;
                font-weight: 600;
            }
            
            /* Buy & Sell Forms - Trading Panels */
            #buyForm, #sellForm {
                background-color: #181A20;
                border: 1px solid #2B3139;
                border-radius: 4px;
            }
            
            #buyTitle {
                color: #0ECB81;
                font-size: 16px;
                font-weight: 700;
                padding: 10px 0px;
            }
            
            #sellTitle {
                color: #F6465D;
                font-size: 16px;
                font-weight: 700;
                padding: 10px 0px;
            }
            
            /* Labels - General Text */
            QLabel {
                color: #EAECEF;
                font-size: 12px;
            }
            
            /* Input Fields */
            QLineEdit {
                background-color: #1E2329;
                color: #EAECEF;
                border: 1px solid #2B3139;
                border-radius: 4px;
                padding: 10px 12px;
                font-size: 13px;
                selection-background-color: #F0B90B;
            }
            
            QLineEdit:hover {
                border: 1px solid #474D57;
            }
            
            QLineEdit:focus {
                border: 1px solid #F0B90B;
                background-color: #1E2329;
            }
            
            QLineEdit::placeholder {
                color: #5E6673;
            }
            
            /* Combo Box - Dropdowns */
            QComboBox {
                background-color: #1E2329;
                color: #EAECEF;
                border: 1px solid #2B3139;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            
            QComboBox:hover {
                border: 1px solid #474D57;
            }
            
            QComboBox:focus {
                border: 1px solid #F0B90B;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #707A8A;
                margin-right: 8px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #1E2329;
                color: #EAECEF;
                border: 1px solid #2B3139;
                selection-background-color: #2B3139;
                selection-color: #F0B90B;
                outline: none;
            }
            
            /* Coin Combo - Special styling for coin selector */
            #coinCombo {
                background-color: #1E2329;
                color: #EAECEF;
                border: 1px solid #2B3139;
                border-radius: 4px;
                padding: 10px 12px;
                font-size: 14px;
                font-weight: 600;
            }
            
            #coinCombo:hover {
                border: 1px solid #F0B90B;
            }
            
            #coinCombo QAbstractItemView {
                background-color: #1E2329;
                color: #EAECEF;
                border: 1px solid #2B3139;
                selection-background-color: #2B3139;
                selection-color: #F0B90B;
                outline: none;
                padding: 8px;
            }
            
            #coinCombo QAbstractItemView::item {
                padding: 8px;
                min-height: 30px;
            }
            
            /* Price Display */
            #priceDisplay {
                color: #848E9C;
                background-color: transparent;
            }
            
            /* Buy Button - Green */
            #buyButton {
                background-color: #0ECB81;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 14px;
                padding: 12px;
            }
            
            #buyButton:hover {
                background-color: #2EE5A0;
            }
            
            #buyButton:pressed {
                background-color: #0AA66E;
            }
            
            /* Sell Button - Red */
            #sellButton {
                background-color: #F6465D;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 14px;
                padding: 12px;
            }
            
            #sellButton:hover {
                background-color: #FF6479;
            }
            
            #sellButton:pressed {
                background-color: #D93A50;
            }
            
            /* Tables - Market List, Order History */
            QTableWidget {
                background-color: transparent;
                color: #EAECEF;
                gridline-color: #2B3139;
                border: none;
                font-size: 12px;
            }
            
            QTableWidget::item {
                padding: 8px 6px;
                border-bottom: 1px solid #2B3139;
            }
            
            QTableWidget::item:selected {
                background-color: #2B3139;
                color: #EAECEF;
            }
            
            QTableWidget::item:hover {
                background-color: #1E2329;
            }
            
            QHeaderView::section {
                background-color: #181A20;
                color: #707A8A;
                padding: 10px 6px;
                border: none;
                border-bottom: 1px solid #2B3139;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
            }
            
            /* Tabs - Order History Tabs */
            QTabWidget::pane {
                border: none;
                background-color: transparent;
                border-top: 1px solid #2B3139;
            }
            
            QTabBar::tab {
                background-color: transparent;
                color: #707A8A;
                padding: 10px 20px;
                border: none;
                font-size: 13px;
                font-weight: 500;
            }
            
            QTabBar::tab:selected {
                background-color: transparent;
                color: #F0B90B;
                border-bottom: 2px solid #F0B90B;
            }
            
            QTabBar::tab:hover:!selected {
                color: #EAECEF;
            }
            
            /* Special Labels */
            #totalValue {
                color: #F0B90B;
                font-weight: 700;
            }
            
            #balanceLabel {
                color: #707A8A;
                font-size: 11px;
                font-weight: 500;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                background-color: transparent;
                width: 6px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #2B3139;
                border-radius: 3px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #474D57;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            
            QScrollBar:horizontal {
                background-color: transparent;
                height: 6px;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #2B3139;
                border-radius: 3px;
                min-width: 30px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #474D57;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* P2P Trading Styles */
            #p2pCreatePanel {
                background-color: #181A20;
                border: 1px solid #2B3139;
                border-radius: 4px;
            }
            
            #p2pCombo {
                background-color: #1E2329;
                color: #EAECEF;
                border: 1px solid #2B3139;
                border-radius: 3px;
                padding: 6px;
                font-size: 11px;
            }
            
            #p2pInput {
                background-color: #1E2329;
                color: #EAECEF;
                border: 1px solid #2B3139;
                border-radius: 3px;
                padding: 6px;
                font-size: 11px;
            }
            
            #createOfferButton {
                background-color: #F0B90B;
                color: #181A20;
                border: none;
                border-radius: 3px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px;
            }
            
            #createOfferButton:hover {
                background-color: #F8D12F;
            }
            
            #p2pOffersTable {
                background-color: transparent;
                color: #EAECEF;
                gridline-color: #2B3139;
                border: none;
                font-size: 11px;
            }
            
            #p2pOffersTable::item {
                padding: 4px;
            }
            
            #p2pOffersTabs {
                background-color: transparent;
            }
            
            #p2pOffersTabs::pane {
                border: none;
                background-color: transparent;
            }
            
            #p2pOffersTabs QTabBar::tab {
                background-color: transparent;
                color: #707A8A;
                padding: 8px 16px;
                border: none;
                font-size: 12px;
                font-weight: 500;
            }
            
            #p2pOffersTabs QTabBar::tab:selected {
                background-color: transparent;
                color: #F0B90B;
                border-bottom: 2px solid #F0B90B;
            }
            
            #acceptOfferButton {
                background-color: #0ECB81;
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                font-weight: 600;
                font-size: 10px;
                padding: 5px 10px;
                min-width: 70px;
            }
            
            #acceptOfferButton:hover {
                background-color: #2EE5A0;
            }
            
            #cancelOfferButton {
                background-color: #F6465D;
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                font-weight: 600;
                font-size: 10px;
                padding: 5px 10px;
                min-width: 70px;
            }
            
            #cancelOfferButton:hover {
                background-color: #FF6479;
            }
            
            /* Portfolio Tab Styles */
            #portfolioTitle {
                color: #F0B90B;
                font-size: 24px;
                font-weight: 700;
            }
            
            #portfolioValueCard {
                background-color: #1E2329;
                border: 1px solid #2B3139;
                border-radius: 8px;
            }
            
            #valueTitle {
                color: #848E9C;
                font-size: 12px;
            }
            
            #totalValue {
                color: #0ECB81;
                font-size: 32px;
                font-weight: 700;
            }
            
            #assetsTitle {
                color: #EAECEF;
                font-size: 16px;
                font-weight: 600;
            }
            
            #portfolioWalletTable {
                background-color: #1E2329;
                color: #EAECEF;
                gridline-color: #2B3139;
                border: 1px solid #2B3139;
                border-radius: 4px;
                font-size: 13px;
            }
            
            #portfolioWalletTable::item {
                padding: 12px;
                border-bottom: 1px solid #2B3139;
            }
            
            #portfolioWalletTable QHeaderView::section {
                background-color: #181A20;
                color: #848E9C;
                border: none;
                border-bottom: 1px solid #2B3139;
                padding: 12px;
                font-weight: 600;
                font-size: 12px;
            }
            
            #refreshButton {
                background-color: #2B3139;
                color: #EAECEF;
                border: 1px solid #474D57;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            
            #refreshButton:hover {
                background-color: #474D57;
                border: 1px solid #F0B90B;
                color: #F0B90B;
            }
        """
    
    def check_for_updates(self):
        """Check for app updates from GitHub."""
        try:
            result = UpdateChecker.check_for_updates()
            
            if result.get('error'):
                # Silent fail - don't bother user with network errors
                print(f"Update check failed: {result['error']}")
                return
            
            if result.get('update_available'):
                # Show update notification
                message = f"""New version available!

Current version: v{result['current_version']}
Latest version: v{result['latest_version']}

{result.get('release_name', 'New Release')}

Would you like to download the update?"""
                
                if styled_dialogs.show_question(self, "Update Available 🚀", message):
                    # Open download URL in browser
                    import webbrowser
                    webbrowser.open(result['download_url'])
            else:
                print(f"App is up to date (v{result['current_version']})")
                
        except Exception as e:
            print(f"Error checking for updates: {e}")
