"""CoinMarketCap API integration for real-time cryptocurrency data."""
import requests
from typing import Dict, Optional, List
from decimal import Decimal
import os
from dotenv import load_dotenv

load_dotenv()


class CoinMarketCapService:
    """Fetches real-time cryptocurrency data from CoinMarketCap API."""
    
    BASE_URL = "https://pro-api.coinmarketcap.com/v1"
    
    # Mapping of symbols to CoinMarketCap IDs
    COIN_MAP = {
        'BTC': 1,
        'ETH': 1027,
        'OP': 11840,
        'BNB': 1839,
        'SOL': 5426,
        'DOGE': 74,
        'TRX': 1958,
        'USDT': 825,
        'XRP': 52,
        'ADA': 2010,
        'LTC': 2,
        'BCH': 1831,
        'XLM': 512,
        'LINK': 1975,
        'MATIC': 3890
    }
    
    def __init__(self):
        """Initialize CoinMarketCap service."""
        self.api_key = os.getenv('COINMARKETCAP_API_KEY')
        if not self.api_key:
            raise ValueError("COINMARKETCAP_API_KEY not found in environment variables")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        })
        self.cache = {}
        self.last_update = {}
    
    def get_price(self, symbol: str, vs_currency: str = 'USD') -> Optional[float]:
        """
        Get current price for a cryptocurrency.
        
        Args:
            symbol: Crypto symbol (BTC, ETH, etc.)
            vs_currency: Quote currency (USD, EUR, etc.)
        
        Returns:
            Current price or None if failed
        """
        if symbol == 'USDT' and vs_currency.upper() == 'USD':
            return 1.0
        
        try:
            coin_id = self.COIN_MAP.get(symbol)
            if not coin_id:
                return None
            
            url = f"{self.BASE_URL}/cryptocurrency/quotes/latest"
            params = {
                'id': coin_id,
                'convert': vs_currency.upper()
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status', {}).get('error_code') == 0:
                coin_data = data['data'][str(coin_id)]
                price = coin_data['quote'][vs_currency.upper()]['price']
                return float(price)
            
            return None
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    def get_multiple_prices(self, symbols: List[str], vs_currency: str = 'USD') -> Dict[str, float]:
        """
        Get prices for multiple cryptocurrencies in one request.
        
        Args:
            symbols: List of crypto symbols
            vs_currency: Quote currency
        
        Returns:
            Dictionary of symbol: price
        """
        try:
            # Filter valid symbols
            valid_ids = [self.COIN_MAP[sym] for sym in symbols if sym in self.COIN_MAP]
            
            if not valid_ids:
                return {}
            
            url = f"{self.BASE_URL}/cryptocurrency/quotes/latest"
            params = {
                'id': ','.join(map(str, valid_ids)),
                'convert': vs_currency.upper()
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            prices = {}
            
            if data.get('status', {}).get('error_code') == 0:
                for coin_id, coin_data in data['data'].items():
                    # Find symbol for this ID
                    for symbol, cid in self.COIN_MAP.items():
                        if cid == int(coin_id):
                            price = coin_data['quote'][vs_currency.upper()]['price']
                            prices[symbol] = float(price)
                            break
            
            return prices
        except Exception as e:
            print(f"Error fetching multiple prices: {e}")
            return {}
    
    def get_pair_price(self, pair: str, vs_currency: str = 'USD') -> Optional[float]:
        """
        Get price for a trading pair (e.g., 'BTC/USDT').
        
        Args:
            pair: Trading pair string
            vs_currency: Quote currency
        
        Returns:
            Current price or None
        """
        try:
            base_symbol = pair.split('/')[0]
            return self.get_price(base_symbol, vs_currency)
        except Exception as e:
            print(f"Error fetching pair price {pair}: {e}")
            return None
    
    def get_market_data(self, symbol: str, vs_currency: str = 'USD') -> Optional[Dict]:
        """
        Get detailed market data for a cryptocurrency.
        
        Args:
            symbol: Crypto symbol
            vs_currency: Quote currency
        
        Returns:
            Dictionary with price, 24h change, market cap, etc.
        """
        try:
            coin_id = self.COIN_MAP.get(symbol)
            if not coin_id:
                return None
            
            url = f"{self.BASE_URL}/cryptocurrency/quotes/latest"
            params = {
                'id': coin_id,
                'convert': vs_currency.upper()
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status', {}).get('error_code') == 0:
                coin_data = data['data'][str(coin_id)]
                quote = coin_data['quote'][vs_currency.upper()]
                
                return {
                    'symbol': symbol,
                    'price': float(quote['price']),
                    'market_cap': float(quote.get('market_cap', 0)),
                    'volume_24h': float(quote.get('volume_24h', 0)),
                    'percent_change_24h': float(quote.get('percent_change_24h', 0)),
                    'percent_change_7d': float(quote.get('percent_change_7d', 0)),
                    'percent_change_30d': float(quote.get('percent_change_30d', 0)),
                }
            
            return None
        except Exception as e:
            print(f"Error fetching market data for {symbol}: {e}")
            return None
    
    def get_ohlcv(self, symbol: str, interval: str = 'daily', limit: int = 100, vs_currency: str = 'USD') -> Optional[List[Dict]]:
        """
        Get OHLCV (Open, High, Low, Close, Volume) data.
        
        Args:
            symbol: Crypto symbol
            interval: Time interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 1w, 15d, 30d)
            limit: Number of data points
            vs_currency: Quote currency
        
        Returns:
            List of OHLCV candles
        """
        try:
            coin_id = self.COIN_MAP.get(symbol)
            if not coin_id:
                return None
            
            url = f"{self.BASE_URL}/cryptocurrency/ohlcv/historical"
            params = {
                'id': coin_id,
                'convert': vs_currency.upper(),
                'time_period': interval,
                'count': limit
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status', {}).get('error_code') == 0:
                quotes = data['data'][str(coin_id)]['quotes']
                
                ohlcv_data = []
                for quote in quotes:
                    timestamp = quote['timestamp']
                    ohlc = quote['quote'][vs_currency.upper()]
                    
                    ohlcv_data.append({
                        'timestamp': timestamp,
                        'open': float(ohlc['open']),
                        'high': float(ohlc['high']),
                        'low': float(ohlc['low']),
                        'close': float(ohlc['close']),
                        'volume': float(ohlc.get('volume', 0))
                    })
                
                return ohlcv_data
            
            return None
        except Exception as e:
            print(f"Error fetching OHLCV data for {symbol}: {e}")
            return None


# Singleton instance
_cmc_service = None


def get_coinmarketcap_service() -> CoinMarketCapService:
    """Get or create CoinMarketCap service instance."""
    global _cmc_service
    if _cmc_service is None:
        try:
            _cmc_service = CoinMarketCapService()
        except ValueError as e:
            print(f"Warning: {e}. Falling back to CoinGecko API.")
            return None
    return _cmc_service
