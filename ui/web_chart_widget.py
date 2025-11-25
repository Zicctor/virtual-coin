"""Web-based chart widget using TradingView lightweight charts."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QHBoxLayout, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QFont
import os
import tempfile


class CoinGeckoChartWidget(QWidget):
    """Widget displaying TradingView's embedded lightweight charts."""
    
    # Mapping of symbols to TradingView symbols
    COIN_MAP = {
        'BTC': 'BTCUSD',
        'ETH': 'ETHUSD',
        'BNB': 'BNBUSD',
        'SOL': 'SOLUSD',
        'XRP': 'XRPUSD',
        'ADA': 'ADAUSD',
        'DOGE': 'DOGEUSD',
        'TRX': 'TRXUSD',
        'OP': 'OPUSD',
        'NEAR': 'NEARUSD',
        'LTC': 'LTCUSD',
        'BCH': 'BCHUSD',
        'XLM': 'XLMUSD',
        'LINK': 'LINKUSD',
        'MATIC': 'MATICUSD',
        'USDT': 'USDTUSD'
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Controls bar
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        # Interval selector
        interval_label = QLabel("Interval:")
        interval_label.setFont(QFont("Segoe UI", 10))
        controls_layout.addWidget(interval_label)
        
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(['1', '5', '15', '60', '240', 'D', 'W'])
        self.interval_combo.setItemText(0, '1m')
        self.interval_combo.setItemText(1, '5m')
        self.interval_combo.setItemText(2, '15m')
        self.interval_combo.setItemText(3, '1h')
        self.interval_combo.setItemText(4, '4h')
        self.interval_combo.setItemText(5, '1D')
        self.interval_combo.setItemText(6, '1W')
        self.interval_combo.setCurrentIndex(3)  # 1h default
        self.interval_combo.currentTextChanged.connect(self.update_chart)
        self.interval_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e2329;
                color: white;
                border: 1px solid #2b3139;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 80px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1e2329;
                color: white;
                selection-background-color: #2b3139;
            }
        """)
        controls_layout.addWidget(self.interval_combo)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Web view for embedded chart
        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("background-color: #0B0E11;")
        
        # Enable JavaScript
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        
        layout.addWidget(self.web_view)
        
        self.setLayout(layout)
        
        # Current coin
        self.current_symbol = 'BTCUSD'
        self.temp_file_path = None
        
    def load_chart(self, symbol: str):
        """Load TradingView chart for the given symbol."""
        trading_symbol = self.COIN_MAP.get(symbol, 'BTCUSD')
        self.current_symbol = trading_symbol
        self.update_chart()
    
    def update_chart(self):
        """Update the chart with current settings."""
        # Map display text to TradingView interval values
        interval_text = self.interval_combo.currentText()
        interval_map = {
            '1m': '1',
            '5m': '5',
            '15m': '15',
            '1h': '60',
            '4h': '240',
            '1D': 'D',
            '1W': 'W'
        }
        interval = interval_map.get(interval_text, '60')
        
        # Use TradingView's simple iframe embed (more reliable)
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #0B0E11;
            overflow: hidden;
        }}
        iframe {{
            border: none;
            width: 100%;
            height: 100vh;
        }}
    </style>
</head>
<body>
    <iframe src="https://s.tradingview.com/embed-widget/advanced-chart/?symbol={self.current_symbol}&interval={interval}&theme=dark&style=1&locale=en&toolbar_bg=%230B0E11&enable_publishing=false&hide_side_toolbar=false&allow_symbol_change=false&watchlist=&details=false&hotlist=false&calendar=false&studies=%5B%5D&support_host=https%3A%2F%2Fwww.tradingview.com" 
            width="100%" 
            height="100%" 
            frameborder="0" 
            allowtransparency="true" 
            scrolling="no">
    </iframe>
</body>
</html>
        """
        
        # Save to temporary file and load
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
            except:
                pass
        
        # Create temp file
        temp_dir = tempfile.gettempdir()
        self.temp_file_path = os.path.join(temp_dir, f'tradingview_chart_{id(self)}.html')
        
        with open(self.temp_file_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Load the file
        self.web_view.setUrl(QUrl.fromLocalFile(self.temp_file_path))
    
    def plot_candlestick(self, data, title=""):
        """Compatibility method - redirects to TradingView chart."""
        # Extract symbol from title (e.g., "BTC/USDT - 1H" -> "BTC")
        if '/' in title:
            symbol = title.split('/')[0]
            self.load_chart(symbol)
    
    def plot_empty(self, message=""):
        """Display empty state."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #0B0E11;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: 'Segoe UI', sans-serif;
            color: #8e99a8;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div>{message or "Select a trading pair to view chart"}</div>
</body>
</html>
        """
        
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
            except:
                pass
        
        temp_dir = tempfile.gettempdir()
        self.temp_file_path = os.path.join(temp_dir, f'tradingview_empty_{id(self)}.html')
        
        with open(self.temp_file_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.web_view.setUrl(QUrl.fromLocalFile(self.temp_file_path))
    
    def __del__(self):
        """Cleanup temp file on destruction."""
        if hasattr(self, 'temp_file_path') and self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
            except:
                pass

