"""Candlestick chart widget using matplotlib with TradingView-style features."""
import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from typing import List, Dict


class CandlestickChartWidget(QWidget):
    """Widget for displaying TradingView-style candlestick charts with indicators."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create matplotlib figure with subplots (main + volume)
        self.figure = Figure(figsize=(12, 7), facecolor='#0B0E11')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Create two subplots: main chart (70%) and volume (30%)
        self.ax_main = self.figure.add_subplot(211)
        self.ax_volume = self.figure.add_subplot(212, sharex=self.ax_main)
        
        # Adjust subplot spacing
        self.figure.subplots_adjust(hspace=0.05, left=0.05, right=0.95, top=0.95, bottom=0.08)
        
        # Add navigation toolbar for zoom/pan/reset
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Apply dark theme
        self.setup_theme()
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Store current data
        self.current_data = []
    
    def setup_theme(self):
        """Apply TradingView-style dark theme to chart."""
        # Background colors
        bg_color = '#0B0E11'
        chart_bg = '#131722'
        grid_color = '#1E222D'
        text_color = '#787B86'
        
        self.ax_main.set_facecolor(chart_bg)
        self.ax_volume.set_facecolor(chart_bg)
        self.figure.patch.set_facecolor(bg_color)
        
        # Grid - subtle like TradingView
        self.ax_main.grid(True, color=grid_color, linestyle='-', linewidth=0.8, alpha=0.6)
        self.ax_volume.grid(True, color=grid_color, linestyle='-', linewidth=0.8, alpha=0.6)
        
        # Remove top and right spines for cleaner look
        self.ax_main.spines['top'].set_visible(False)
        self.ax_main.spines['right'].set_visible(False)
        self.ax_main.spines['left'].set_color(grid_color)
        self.ax_main.spines['bottom'].set_color(grid_color)
        
        self.ax_volume.spines['top'].set_visible(False)
        self.ax_volume.spines['right'].set_visible(False)
        self.ax_volume.spines['left'].set_color(grid_color)
        self.ax_volume.spines['bottom'].set_color(grid_color)
        
        # Tick labels
        self.ax_main.tick_params(colors=text_color, labelsize=9)
        self.ax_volume.tick_params(colors=text_color, labelsize=9)
        
        # Remove x-axis labels from main chart (shared with volume)
        self.ax_main.tick_params(labelbottom=False)
    
    def calculate_ma(self, closes: List[float], period: int) -> np.ndarray:
        """Calculate moving average."""
        if len(closes) < period:
            return np.array([np.nan] * len(closes))
        
        ma = np.convolve(closes, np.ones(period), 'valid') / period
        # Pad with NaN for alignment
        return np.concatenate([np.full(period - 1, np.nan), ma])
    
    def plot_candlestick(self, data: List[Dict], title: str = "Price Chart"):
        """
        Plot TradingView-style candlestick chart with moving averages and volume.
        
        Args:
            data: List of candle dictionaries with timestamp, open, high, low, close, volume
            title: Chart title
        """
        if not data:
            self.plot_empty("No data available")
            return
        
        self.current_data = data
        self.ax_main.clear()
        self.ax_volume.clear()
        self.setup_theme()
        
        try:
            # Extract data
            timestamps = [datetime.fromtimestamp(int(d['timestamp']) / 1000) for d in data]
            opens = np.array([float(d['open']) for d in data])
            highs = np.array([float(d['high']) for d in data])
            lows = np.array([float(d['low']) for d in data])
            closes = np.array([float(d['close']) for d in data])
            volumes = np.array([float(d.get('volume', 0)) for d in data])
            
            # Convert timestamps to matplotlib dates
            dates = mdates.date2num(timestamps)
            
            # TradingView colors
            green = '#26a69a'  # Bullish
            red = '#ef5350'    # Bearish
            
            # Plot candlesticks
            candle_width = 0.6 / len(dates) if len(dates) > 50 else 0.008
            
            for i in range(len(dates)):
                date = dates[i]
                o, h, l, c = opens[i], highs[i], lows[i], closes[i]
                
                # Determine color
                color = green if c >= o else red
                
                # High-low line (wick)
                self.ax_main.plot([date, date], [l, h], color=color, linewidth=1.2, alpha=0.8)
                
                # Open-close body
                body_height = abs(c - o)
                body_bottom = min(o, c)
                
                if body_height > 0:
                    self.ax_main.bar(date, body_height, width=candle_width, bottom=body_bottom,
                                   color=color, edgecolor=color, alpha=0.9)
                else:
                    # Doji - draw horizontal line
                    self.ax_main.plot([date - candle_width/2, date + candle_width/2], [c, c],
                                    color=color, linewidth=1.5)
            
            # Calculate and plot moving averages (MA7, MA25, MA99 like TradingView)
            ma7 = self.calculate_ma(closes.tolist(), 7)
            ma25 = self.calculate_ma(closes.tolist(), 25)
            ma99 = self.calculate_ma(closes.tolist(), 99)
            
            # Plot MAs with TradingView colors
            if len(closes) >= 7:
                self.ax_main.plot(dates, ma7, color='#2962FF', linewidth=1.5, alpha=0.9, label='MA(7)')
            if len(closes) >= 25:
                self.ax_main.plot(dates, ma25, color='#FF6D00', linewidth=1.5, alpha=0.9, label='MA(25)')
            if len(closes) >= 99:
                self.ax_main.plot(dates, ma99, color='#E040FB', linewidth=1.5, alpha=0.9, label='MA(99)')
            
            # Add legend for MAs
            if len(closes) >= 7:
                legend = self.ax_main.legend(loc='upper left', frameon=True, facecolor='#131722',
                                           edgecolor='#2B2B43', fontsize=9, labelcolor='#787B86')
                legend.get_frame().set_alpha(0.9)
            
            # Format main chart
            self.ax_main.set_ylabel('Price (USDT)', color='#787B86', fontsize=10, fontweight='bold')
            self.ax_main.margins(x=0.02, y=0.1)
            
            # Volume bars
            for i in range(len(dates)):
                color = green if closes[i] >= opens[i] else red
                self.ax_volume.bar(dates[i], volumes[i], width=candle_width, color=color, alpha=0.6)
            
            # Format volume chart
            self.ax_volume.set_ylabel('Volume', color='#787B86', fontsize=9)
            self.ax_volume.set_xlabel('Time', color='#787B86', fontsize=9)
            
            # Format x-axis with better date formatting
            self.ax_volume.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            self.ax_volume.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.figure.autofmt_xdate(rotation=0, ha='center')
            
            # Add title with current price info
            if len(closes) > 0:
                current_price = closes[-1]
                price_change = closes[-1] - closes[0]
                price_change_pct = (price_change / closes[0]) * 100
                change_color = green if price_change >= 0 else red
                
                title_text = f"{title}  ${current_price:,.2f}  "
                change_text = f"{'+' if price_change >= 0 else ''}{price_change_pct:.2f}%"
                
                self.ax_main.set_title(title_text, color='#D1D4DC', fontsize=12, 
                                      fontweight='bold', loc='left', pad=10)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error plotting candlestick chart: {e}")
            import traceback
            traceback.print_exc()
            self.plot_empty(f"Error: {str(e)}")
    
    def plot_line(self, data: List[Dict], title: str = "Price Chart"):
        """
        Plot simple line chart using close prices.
        
        Args:
            data: List of candle dictionaries
            title: Chart title
        """
        if not data:
            self.plot_empty("No data available")
            return
        
        self.current_data = data
        self.ax.clear()
        self.setup_theme()
        
        try:
            # Extract data
            timestamps = [datetime.fromtimestamp(int(d['timestamp'])) for d in data]
            closes = [float(d['close']) for d in data]
            
            # Plot line
            self.ax.plot(timestamps, closes, color='#F0B90B', linewidth=2)
            
            # Fill area under line
            self.ax.fill_between(timestamps, closes, alpha=0.1, color='#F0B90B')
            
            # Format x-axis
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.figure.autofmt_xdate(rotation=45, ha='right')
            
            # Set labels
            self.ax.set_xlabel('Time', color='#848E9C', fontsize=9)
            self.ax.set_ylabel('Price (USDT)', color='#848E9C', fontsize=9)
            self.ax.set_title(title, color='#EAECEF', fontsize=10, pad=10)
            
            # Margins
            self.ax.margins(x=0.01)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error plotting line chart: {e}")
            self.plot_empty(f"Error: {str(e)}")
    
    def plot_empty(self, message: str = "No data available"):
        """Display message when no data is available."""
        self.ax_main.clear()
        self.ax_volume.clear()
        self.setup_theme()
        
        self.ax_main.text(0.5, 0.5, message, 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax_main.transAxes,
                        color='#787B86',
                        fontsize=14)
        
        self.ax_main.set_xticks([])
        self.ax_main.set_yticks([])
        self.ax_volume.set_xticks([])
        self.ax_volume.set_yticks([])
        
        self.canvas.draw()
    
    def refresh(self):
        """Refresh the chart with current data."""
        if self.current_data:
            self.plot_candlestick(self.current_data)
