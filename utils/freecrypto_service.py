"""FreeCryptoAPI service for OHLCV candlestick data."""
import requests
import os
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from config import Config
import time


class FreeCryptoAPIService:
    """Fetches OHLCV candlestick data from FreeCryptoAPI with caching and rate limiting."""
    
    def __init__(self):
        """Initialize the FreeCryptoAPI service."""
        # Check if simulator mode is enabled (default to false - use real API)
        use_simulator = os.getenv('USE_SIMULATOR', 'false').lower() == 'true'
        
        if use_simulator:
            from utils.price_simulator import get_price_simulator
            self.simulator = get_price_simulator()
            self.mode = 'simulator'
            return
        
        # API mode setup
        self.mode = 'api'
        self.base_url = Config.FREECRYPTO_BASE_URL
        self.api_key = Config.FREECRYPTO_API_KEY
        self.session = requests.Session()
        
        # Caching to reduce API calls
        self.cache = {}  # Cache stored data
        self.cache_timestamp = {}  # Track when data was cached
        
        # Cache duration based on interval (longer intervals = longer cache)
        self.cache_durations = {
            '1m': 30,    # Cache 1-minute data for 30 seconds
            '5m': 120,   # Cache 5-minute data for 2 minutes
            '15m': 300,  # Cache 15-minute data for 5 minutes
            '1h': 900,   # Cache 1-hour data for 15 minutes
            '4h': 1800,  # Cache 4-hour data for 30 minutes
            '1d': 3600   # Cache daily data for 1 hour
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        
        # Set default headers
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
        
        # Add CoinGecko API key if available (for fallback requests)
        coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        if coingecko_api_key:
            self.session.headers.update({
                'x-cg-demo-api-key': coingecko_api_key
            })
    
    def _is_cached(self, cache_key: str, interval: str) -> bool:
        """Check if data is still valid in cache."""
        if cache_key not in self.cache or cache_key not in self.cache_timestamp:
            return False
        
        cache_duration = self.cache_durations.get(interval, 300)  # Default 5 minutes
        elapsed = (datetime.now() - self.cache_timestamp[cache_key]).total_seconds()
        return elapsed < cache_duration
    
    def _wait_for_rate_limit(self):
        """Enforce minimum time between API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_ohlcv(self, symbol: str, interval: str = '1h', limit: int = 100) -> Optional[List[Dict]]:
        """
        Get OHLCV (candlestick) data for a cryptocurrency with caching.
        Uses simulator or FreeCryptoAPI based on mode.
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            interval: Time interval ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to fetch (max 1000)
        
        Returns:
            List of OHLCV data dictionaries or None if failed
        """
        # Simulator mode
        if self.mode == 'simulator':
            return self.simulator.get_ohlcv(symbol, interval, limit)
        
        # API mode
        if not self.api_key:
            # Fallback to CoinGecko for OHLCV data (free, no API key needed)
            return self._get_ohlcv_from_coingecko(symbol, interval, limit)
        
        # Check cache first
        cache_key = f"{symbol}_{interval}_{limit}"
        if self._is_cached(cache_key, interval):
            print(f"Using cached data for {symbol} {interval}")
            return self.cache[cache_key]
        
        # Rate limiting - don't spam API
        self._wait_for_rate_limit()
        
        try:
            # Map interval format to FreeCryptoAPI format
            interval_map = {
                '1m': '1m',
                '5m': '5m',
                '15m': '15m',
                '1h': '1h',
                '4h': '4h',
                '1d': '1d'
            }
            
            # Use /getOHLC endpoint
            endpoint = f"{self.base_url}/getOHLC"
            
            params = {
                'symbol': symbol.upper(),
                'interval': interval_map.get(interval, '1h'),
                'limit': limit
            }
            
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response based on FreeCryptoAPI format
            if isinstance(data, dict) and 'data' in data:
                result = data['data']
            elif isinstance(data, list):
                result = data
            else:
                result = data
            
            # Cache the result
            if result:
                self.cache[cache_key] = result
                self.cache_timestamp[cache_key] = datetime.now()
                print(f"Cached new data for {symbol} {interval} (valid for {self.cache_durations.get(interval, 300)}s)")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching OHLCV data from FreeCryptoAPI: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def get_candles_for_pair(self, pair: str, interval: str = '1h', limit: int = 100) -> Optional[List[Dict]]:
        """
        Get candlestick data for a trading pair.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            interval: Time interval
            limit: Number of candles
        
        Returns:
            List of candle data or None
        """
        try:
            # Extract base currency from pair
            base = pair.split('/')[0]
            return self.get_ohlcv(base, interval, limit)
        except Exception as e:
            print(f"Error getting candles for pair {pair}: {e}")
            return None
    
    def format_for_chart(self, ohlcv_data: List[Dict]) -> List[Dict]:
        """
        Format OHLCV data for charting.
        
        Args:
            ohlcv_data: Raw OHLCV data from API
        
        Returns:
            Formatted data with timestamp, open, high, low, close, volume
        """
        if not ohlcv_data:
            return []
        
        formatted = []
        
        for candle in ohlcv_data:
            try:
                # Handle different possible formats
                if isinstance(candle, dict):
                    formatted_candle = {
                        'timestamp': candle.get('timestamp') or candle.get('time') or candle.get('date'),
                        'open': float(candle.get('open', 0)),
                        'high': float(candle.get('high', 0)),
                        'low': float(candle.get('low', 0)),
                        'close': float(candle.get('close', 0)),
                        'volume': float(candle.get('volume', 0))
                    }
                    formatted.append(formatted_candle)
                elif isinstance(candle, (list, tuple)) and len(candle) >= 6:
                    # [timestamp, open, high, low, close, volume]
                    formatted_candle = {
                        'timestamp': candle[0],
                        'open': float(candle[1]),
                        'high': float(candle[2]),
                        'low': float(candle[3]),
                        'close': float(candle[4]),
                        'volume': float(candle[5])
                    }
                    formatted.append(formatted_candle)
            except (ValueError, KeyError, IndexError) as e:
                print(f"Error formatting candle: {e}")
                continue
        
        return formatted
    
    def generate_mock_data(self, symbol: str = 'BTC', interval: str = '1h', limit: int = 100) -> List[Dict]:
        """
        Generate mock OHLCV data for testing when API is unavailable.
        
        Args:
            symbol: Crypto symbol
            interval: Time interval
            limit: Number of candles
        
        Returns:
            Mock OHLCV data
        """
        import random
        
        # Base prices
        base_prices = {
            'BTC': 45000,
            'ETH': 3200,
            'BNB': 350,
            'XRP': 0.6,
            'ADA': 0.5,
            'SOL': 100,
            'DOT': 7
        }
        
        base_price = base_prices.get(symbol, 1000)
        
        # Time intervals in seconds
        intervals_map = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        
        interval_seconds = intervals_map.get(interval, 3600)
        
        candles = []
        current_time = datetime.now()
        current_price = base_price
        
        for i in range(limit):
            # Calculate timestamp (going backwards in time)
            timestamp = int((current_time - timedelta(seconds=interval_seconds * (limit - i))).timestamp())
            
            # Generate realistic OHLC with random walk
            price_change = random.uniform(-0.02, 0.02)  # ±2% change
            new_price = current_price * (1 + price_change)
            
            # Generate OHLC
            open_price = current_price
            close_price = new_price
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.01)
            low_price = min(open_price, close_price) * random.uniform(0.99, 1.0)
            volume = random.uniform(100, 10000)
            
            candles.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': round(volume, 2)
            })
            
            current_price = new_price
        
        return candles
    
    def _get_ohlcv_from_coingecko(self, symbol: str, interval: str = '1h', limit: int = 100) -> Optional[List[Dict]]:
        """
        Get OHLCV data from CoinGecko API (free, no API key needed).
        
        Args:
            symbol: Crypto symbol (BTC, ETH, etc.)
            interval: Time interval
            limit: Number of candles
        
        Returns:
            List of OHLCV candles
        """
        # CoinGecko coin ID mapping
        coin_map = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin',
            'SOL': 'solana', 'XRP': 'ripple', 'ADA': 'cardano',
            'DOGE': 'dogecoin', 'TRX': 'tron', 'OP': 'optimism',
            'NEAR': 'near', 'LTC': 'litecoin', 'BCH': 'bitcoin-cash',
            'XLM': 'stellar', 'LINK': 'chainlink', 'MATIC': 'polygon-ecosystem-token',
            'USDT': 'tether'
        }
        
        coin_id = coin_map.get(symbol)
        if not coin_id:
            return None
        
        try:
            # Determine days based on interval
            # CoinGecko auto-determines interval based on days:
            # - days 1: 5-minute data
            # - days 2-90: hourly data (automatic)
            # - days >90: daily data (automatic)
            interval_days_map = {
                '1h': 2,      # 2 days gets hourly data automatically
                '4h': 7,      # 7 days gets hourly data, we'll sample every 4th
                '1d': 90,     # 90 days gets hourly data, we'll aggregate to daily
                '1w': 365     # 365 days gets daily data, we'll aggregate to weekly
            }
            days = interval_days_map.get(interval, 7)
            
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days
                # Don't specify 'interval' - let CoinGecko auto-determine based on 'days'
            }
            
            # Add headers to avoid 401
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            
            # If 401, try alternative approach with historical database
            if response.status_code == 401:
                print(f"CoinGecko API error, using historical database for {symbol}")
                return self._get_ohlcv_from_historical_db(symbol, interval, limit)
            
            response.raise_for_status()
            data = response.json()
            
            # Determine what interval we actually got based on days
            if days == 1:
                actual_interval = '5m'
            elif days <= 90:
                actual_interval = 'hourly'
            else:
                actual_interval = 'daily'
            
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])
            
            if not prices:
                return None
            
            # Convert to OHLCV format
            candles = []
            
            # For 1h interval, use hourly data directly (from days=2)
            if interval == '1h':
                for i in range(len(prices)):
                    timestamp_ms = prices[i][0]
                    price = prices[i][1]
                    volume = volumes[i][1] if i < len(volumes) else 0
                    
                    # Simulate OHLC from single price point
                    variance = price * 0.005
                    candles.append({
                        'timestamp': timestamp_ms,
                        'open': round(price - variance * 0.5, 2),
                        'high': round(price + variance, 2),
                        'low': round(price - variance, 2),
                        'close': round(price, 2),
                        'volume': round(volume, 2)
                    })
            
            # For 4h interval, aggregate every 4 hourly candles (from days=7)
            elif interval == '4h' and actual_interval == 'hourly':
                for i in range(0, len(prices) - 3, 4):
                    four_prices = [prices[j][1] for j in range(i, min(i+4, len(prices)))]
                    timestamp_ms = prices[i][0]
                    volume = sum(volumes[j][1] for j in range(i, min(i+4, len(volumes)))) if i < len(volumes) else 0
                    
                    candles.append({
                        'timestamp': timestamp_ms,
                        'open': round(four_prices[0], 2),
                        'high': round(max(four_prices), 2),
                        'low': round(min(four_prices), 2),
                        'close': round(four_prices[-1], 2),
                        'volume': round(volume, 2)
                    })
            
            # For 1d interval, aggregate 24 hourly candles to daily (from days=90)
            elif interval == '1d' and actual_interval == 'hourly':
                for i in range(0, len(prices) - 23, 24):
                    day_prices = [prices[j][1] for j in range(i, min(i+24, len(prices)))]
                    timestamp_ms = prices[i][0]
                    volume = sum(volumes[j][1] for j in range(i, min(i+24, len(volumes)))) if i < len(volumes) else 0
                    
                    candles.append({
                        'timestamp': timestamp_ms,
                        'open': round(day_prices[0], 2),
                        'high': round(max(day_prices), 2),
                        'low': round(min(day_prices), 2),
                        'close': round(day_prices[-1], 2),
                        'volume': round(volume, 2)
                    })
            
            # For 1w interval, aggregate every 7 daily candles (from days=365)
            elif interval == '1w' and actual_interval == 'daily':
                for i in range(0, len(prices) - 6, 7):
                    week_prices = [prices[j][1] for j in range(i, min(i+7, len(prices)))]
                    timestamp_ms = prices[i][0]
                    volume = sum(volumes[j][1] for j in range(i, min(i+7, len(volumes)))) if i < len(volumes) else 0
                    
                    candles.append({
                        'timestamp': timestamp_ms,
                        'open': round(week_prices[0], 2),
                        'high': round(max(week_prices), 2),
                        'low': round(min(week_prices), 2),
                        'close': round(week_prices[-1], 2),
                        'volume': round(volume, 2)
                    })
            
            # Fallback: use data as-is
            else:
                for i in range(len(prices)):
                    timestamp_ms = prices[i][0]
                    price = prices[i][1]
                    volume = volumes[i][1] if i < len(volumes) else 0
                    
                    variance = price * 0.005
                    candles.append({
                        'timestamp': timestamp_ms,
                        'open': round(price - variance * 0.5, 2),
                        'high': round(price + variance, 2),
                        'low': round(price - variance, 2),
                        'close': round(price, 2),
                        'volume': round(volume, 2)
                    })
            
            return candles[-limit:] if len(candles) > limit else candles
            
        except Exception as e:
            print(f"Error fetching OHLCV from CoinGecko for {symbol}: {e}")
            # Fallback to historical database
            print(f"Falling back to historical database for {symbol}")
            return self._get_ohlcv_from_historical_db(symbol, interval, limit)
    
    def _get_ohlcv_from_historical_db(self, symbol: str, interval: str = '1h', limit: int = 200) -> Optional[List[Dict]]:
        """
        Get OHLCV data from historical database (Supabase).
        Used as fallback when CoinGecko API fails.
        """
        try:
            from utils.historical_data_fetcher import get_historical_data
            from datetime import datetime, timedelta
            
            # Map symbol to coin_id
            coin_map = {
                'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin',
                'SOL': 'solana', 'XRP': 'ripple', 'ADA': 'cardano',
                'DOGE': 'dogecoin', 'TRX': 'tron', 'OP': 'optimism',
                'NEAR': 'near', 'LTC': 'litecoin', 'BCH': 'bitcoin-cash',
                'XLM': 'stellar', 'LINK': 'chainlink', 'MATIC': 'polygon-ecosystem-token',
                'USDT': 'tether'
            }
            
            coin_id = coin_map.get(symbol)
            if not coin_id:
                return None
            
            # Determine days to fetch based on interval
            interval_days = {
                '1h': 7,
                '4h': 30,
                '1d': 365,
                '1w': 365
            }
            days = interval_days.get(interval, 7)
            
            # Get historical data from database
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            historical_data = get_historical_data(coin_id, start_date, end_date)
            
            if not historical_data:
                print(f"No historical data found for {symbol}")
                return None
            
            # Convert to OHLCV format and aggregate based on interval
            candles = []
            
            if interval == '1d':
                # Use daily data as-is
                for record in historical_data:
                    candles.append({
                        'timestamp': int(record['timestamp'].timestamp() * 1000),
                        'open': record['price'],
                        'high': record['price'] * 1.005,  # Simulate with small variance
                        'low': record['price'] * 0.995,
                        'close': record['price'],
                        'volume': 0  # Volume not stored in historical DB
                    })
            
            elif interval == '1w':
                # Aggregate to weekly
                for i in range(0, len(historical_data) - 6, 7):
                    week_data = historical_data[i:i+7]
                    prices = [d['price'] for d in week_data]
                    candles.append({
                        'timestamp': int(week_data[0]['timestamp'].timestamp() * 1000),
                        'open': prices[0],
                        'high': max(prices),
                        'low': min(prices),
                        'close': prices[-1],
                        'volume': 0
                    })
            
            else:
                # For hourly/4h, use daily data with interpolation
                for record in historical_data:
                    price = record['price']
                    candles.append({
                        'timestamp': int(record['timestamp'].timestamp() * 1000),
                        'open': price * 0.998,
                        'high': price * 1.003,
                        'low': price * 0.997,
                        'close': price,
                        'volume': 0
                    })
            
            return candles[-limit:] if len(candles) > limit else candles
            
        except Exception as e:
            print(f"Error fetching from historical database for {symbol}: {e}")
            return None


# Singleton instance
_freecrypto_service = None

def get_freecrypto_service() -> FreeCryptoAPIService:
    """Get the global FreeCryptoAPI service instance."""
    global _freecrypto_service
    if _freecrypto_service is None:
        _freecrypto_service = FreeCryptoAPIService()
    return _freecrypto_service
