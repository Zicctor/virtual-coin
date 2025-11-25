"""Realistic cryptocurrency price simulator for trading game."""
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math


class PriceSimulator:
    """
    Simulates realistic cryptocurrency price movements.
    Uses random walk with volatility and trend patterns.
    """
    
    # Base prices (approximate real values as starting point)
    BASE_PRICES = {
        'BTC': 45000.0,
        'ETH': 2500.0,
        'BNB': 320.0,
        'SOL': 120.0,
        'XRP': 0.65,
        'ADA': 0.45,
        'DOGE': 0.08,
        'TRX': 0.12,
        'OP': 2.5,
        'NEAR': 5.5,
        'LTC': 85.0,
        'BCH': 250.0,
        'XLM': 0.13,
        'LINK': 15.0,
        'MATIC': 0.85,
        'USDT': 1.0
    }
    
    # Volatility factors (how much each coin can fluctuate)
    VOLATILITY = {
        'BTC': 0.02,   # 2% max change per update
        'ETH': 0.025,  # 2.5%
        'BNB': 0.03,
        'SOL': 0.04,
        'XRP': 0.035,
        'ADA': 0.04,
        'DOGE': 0.06,  # More volatile
        'TRX': 0.045,
        'OP': 0.05,
        'NEAR': 0.045,
        'LTC': 0.025,
        'BCH': 0.03,
        'XLM': 0.04,
        'LINK': 0.035,
        'MATIC': 0.045,
        'USDT': 0.0001  # Stable coin
    }
    
    def __init__(self):
        """Initialize the price simulator."""
        self.current_prices = self.BASE_PRICES.copy()
        self.price_history = {symbol: [] for symbol in self.BASE_PRICES.keys()}
        self.trends = {symbol: 0.0 for symbol in self.BASE_PRICES.keys()}  # -1 to 1
        self.last_update = datetime.now()
        self.session_start = datetime.now()
        
        # Generate initial 24h price changes
        self.price_changes_24h = {}
        for symbol in self.BASE_PRICES.keys():
            if symbol == 'USDT':
                self.price_changes_24h[symbol] = 0.0
            else:
                self.price_changes_24h[symbol] = random.uniform(-15, 15)
    
    def get_price(self, symbol: str, vs_currency: str = 'usd') -> Optional[float]:
        """
        Get current simulated price for a cryptocurrency.
        
        Args:
            symbol: Crypto symbol (BTC, ETH, etc.)
            vs_currency: Quote currency (ignored, always USD)
        
        Returns:
            Current simulated price
        """
        if symbol == 'USDT':
            return 1.0
        
        return self.current_prices.get(symbol)
    
    def get_multiple_prices(self, symbols: List[str], vs_currency: str = 'usd') -> Dict[str, float]:
        """
        Get prices for multiple cryptocurrencies.
        
        Args:
            symbols: List of crypto symbols
            vs_currency: Quote currency (ignored)
        
        Returns:
            Dict mapping symbol to price
        """
        return {symbol: self.get_price(symbol) for symbol in symbols if symbol in self.current_prices}
    
    def get_pair_price(self, pair: str) -> Optional[float]:
        """
        Get price for a trading pair.
        
        Args:
            pair: Trading pair string (e.g., 'BTC/USDT')
        
        Returns:
            Current price
        """
        try:
            base, quote = pair.split('/')
            if quote == 'USDT' or quote == 'USD':
                return self.get_price(base)
            
            # Calculate cross rate
            base_price = self.get_price(base)
            quote_price = self.get_price(quote)
            
            if base_price and quote_price:
                return base_price / quote_price
            
            return None
        except Exception as e:
            print(f"Error getting pair price for {pair}: {e}")
            return None
    
    def get_24h_change(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Get 24h price change data.
        
        Args:
            symbol: Crypto symbol
        
        Returns:
            Dict with price_change_24h and price_change_percentage_24h
        """
        if symbol not in self.current_prices:
            return None
        
        current_price = self.current_prices[symbol]
        change_pct = self.price_changes_24h.get(symbol, 0)
        price_change = current_price * (change_pct / 100)
        
        return {
            'price_change_24h': price_change,
            'price_change_percentage_24h': change_pct,
            'current_price': current_price
        }
    
    def update_prices(self):
        """
        Update all prices with realistic random movements.
        Uses random walk with trends and mean reversion.
        """
        now = datetime.now()
        time_delta = (now - self.last_update).total_seconds()
        
        # Update prices
        for symbol in self.current_prices.keys():
            if symbol == 'USDT':
                continue  # Stable coin stays at $1
            
            current_price = self.current_prices[symbol]
            volatility = self.VOLATILITY[symbol]
            
            # Random walk component
            random_change = random.uniform(-volatility, volatility)
            
            # Trend component (gradually shifts between -1 and 1)
            if random.random() < 0.1:  # 10% chance to shift trend
                self.trends[symbol] = random.uniform(-1, 1)
            
            trend_influence = self.trends[symbol] * volatility * 0.3
            
            # Mean reversion (pull back towards base price)
            base_price = self.BASE_PRICES[symbol]
            deviation = (current_price - base_price) / base_price
            mean_reversion = -deviation * 0.05  # 5% pull back
            
            # Combine all factors
            total_change = random_change + trend_influence + mean_reversion
            
            # Apply change
            new_price = current_price * (1 + total_change)
            
            # Ensure price doesn't go too far from base (±50%)
            min_price = base_price * 0.5
            max_price = base_price * 1.5
            new_price = max(min_price, min(max_price, new_price))
            
            self.current_prices[symbol] = new_price
            
            # Update 24h change (slowly evolve over time)
            if random.random() < 0.3:  # 30% chance to update 24h change
                self.price_changes_24h[symbol] += random.uniform(-2, 2)
                # Keep within reasonable bounds
                self.price_changes_24h[symbol] = max(-30, min(30, self.price_changes_24h[symbol]))
        
        self.last_update = now
    
    def get_ohlcv(self, symbol: str, interval: str = '1h', limit: int = 100, vs_currency: str = 'USD') -> Optional[List[Dict]]:
        """
        Generate simulated OHLCV (candlestick) data.
        
        Args:
            symbol: Crypto symbol
            interval: Time interval
            limit: Number of candles to generate
        
        Returns:
            List of OHLCV candles
        """
        if symbol not in self.current_prices:
            return None
        
        # Interval to minutes mapping
        interval_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, '6h': 360,
            '8h': 480, '12h': 720, '1d': 1440, '1w': 10080
        }
        
        minutes = interval_minutes.get(interval, 60)
        current_price = self.current_prices[symbol]
        volatility = self.VOLATILITY[symbol]
        
        candles = []
        now = datetime.now()
        
        # Start from current price and work backwards
        price = current_price
        
        for i in range(limit):
            # Calculate timestamp
            timestamp = now - timedelta(minutes=minutes * (limit - i - 1))
            
            # Generate OHLC with realistic patterns
            # Open
            open_price = price
            
            # Random price movement for this candle
            change_range = volatility * random.uniform(0.5, 1.5)
            
            # High and Low
            high_price = open_price * (1 + random.uniform(0, change_range))
            low_price = open_price * (1 - random.uniform(0, change_range))
            
            # Close (biased towards trend)
            trend_bias = self.trends.get(symbol, 0) * 0.3
            close_change = random.uniform(-change_range, change_range) + trend_bias
            close_price = open_price * (1 + close_change)
            
            # Ensure high is highest, low is lowest
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            # Volume (random but realistic)
            base_volume = self.BASE_PRICES[symbol] * random.uniform(1000000, 5000000)
            volume = base_volume * random.uniform(0.5, 2.0)
            
            # Convert timestamp to Unix timestamp in milliseconds (for chart compatibility)
            unix_timestamp = int(timestamp.timestamp() * 1000)
            
            candles.append({
                'timestamp': unix_timestamp,
                'open': round(open_price, 8),
                'high': round(high_price, 8),
                'low': round(low_price, 8),
                'close': round(close_price, 8),
                'volume': round(volume, 2)
            })
            
            # Update price for next candle (with random walk)
            price = close_price * (1 + random.uniform(-volatility * 0.5, volatility * 0.5))
        
        return candles
    
    def format_for_chart(self, ohlcv_data: List[Dict]) -> List[Dict]:
        """
        Format OHLCV data for chart display (already in correct format).
        """
        return ohlcv_data
    
    def get_api_usage_stats(self) -> Dict:
        """
        Get API usage statistics (always zero for simulator).
        """
        return {
            'calls_made': 0,
            'calls_limit': 0,
            'calls_remaining': float('inf'),
            'usage_percentage': 0,
            'reset_date': None,
            'mode': 'simulator'
        }
    
    def clear_cache(self):
        """Clear cache (no-op for simulator)."""
        pass


# Singleton instance
_price_simulator = None


def get_price_simulator() -> PriceSimulator:
    """Get or create price simulator instance."""
    global _price_simulator
    if _price_simulator is None:
        _price_simulator = PriceSimulator()
    return _price_simulator
