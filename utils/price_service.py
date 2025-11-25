"""Real-time cryptocurrency price service with CoinMarketCap fallback."""
import requests
from typing import Dict, Optional, List
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class PriceService:
    """Fetches real-time cryptocurrency prices from CoinMarketCap with CoinGecko fallback or uses simulator."""
    
    # CoinMarketCap API (requires API key)
    CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"
    
    # CoinGecko API (free, no API key required - fallback)
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Mapping of our currency symbols to CoinMarketCap IDs
    CMC_COIN_MAP = {
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
    
    # Mapping of our currency symbols to CoinGecko IDs (fallback)
    COINGECKO_COIN_IDS = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'BNB': 'binancecoin',
        'SOL': 'solana',
        'XRP': 'ripple',
        'ADA': 'cardano',
        'DOGE': 'dogecoin',
        'TRX': 'tron',
        'OP': 'optimism',
        'NEAR': 'near',
        'LTC': 'litecoin',
        'BCH': 'bitcoin-cash',
        'XLM': 'stellar',
        'LINK': 'chainlink',
        'MATIC': 'polygon-ecosystem-token',  # Updated from matic-network to new ID
        'USDT': 'tether'
    }
    
    def __init__(self):
        """Initialize the price service."""
        # Check for simulator mode (set USE_SIMULATOR=true in .env to use game mode)
        # Default to false (use real API data)
        use_simulator = os.getenv('USE_SIMULATOR', 'false').lower() == 'true'
        
        if use_simulator:
            # Use simulator mode - no API calls needed
            from utils.price_simulator import get_price_simulator
            self.simulator = get_price_simulator()
            self.mode = 'simulator'
            return
        
        # API mode
        self.mode = 'api'
        self.simulator = None
        self.session = requests.Session()
        # Add user-agent to avoid 401 errors
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.cache = {}
        self.cache_timestamp = {}
        self.cache_duration = 180  # Cache for 3 minutes (optimized for multi-user)
        
        # Rate limiting tracking for CoinMarketCap Basic Plan
        # Monthly limit: 10,000 calls/month (hard cap)
        self.api_call_count = 0
        self.api_call_limit_monthly = 10000
        self.api_call_reset_date = None
        self.rate_limit_warning_shown = False
        
        # Per-minute rate limit: 30 requests/minute
        self.api_calls_per_minute = []
        self.api_call_limit_per_minute = 30
        
        # Try to load CoinMarketCap API key
        self.cmc_api_key = os.getenv('COINMARKETCAP_API_KEY')
        self.use_cmc = bool(self.cmc_api_key)
        
        # Try to load CoinGecko API key
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        if self.coingecko_api_key:
            self.session.headers.update({
                'x-cg-demo-api-key': self.coingecko_api_key
            })
            print("✓ CoinGecko API key loaded")
        
        if self.use_cmc:
            # Setup CoinMarketCap headers
            self.cmc_headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': self.cmc_api_key,
            }
            print("✓ CoinMarketCap API enabled")
            print("  - Monthly limit: 10,000 calls")
            print("  - Per-minute limit: 30 requests")
            print("  - Cache duration: 60 seconds")
        else:
            print("⚠ CoinMarketCap API key not found. Using CoinGecko (free tier) as fallback.")
    
    def get_price(self, symbol: str, vs_currency: str = 'usd') -> Optional[float]:
        """
        Get current price for a cryptocurrency.
        Uses simulator or tries CoinMarketCap first, falls back to CoinGecko.
        
        Args:
            symbol: Crypto symbol (BTC, ETH, etc.)
            vs_currency: Quote currency (usd, eur, etc.)
        
        Returns:
            Current price or None if failed
        """
        # Simulator mode
        if self.mode == 'simulator':
            return self.simulator.get_price(symbol, vs_currency)
        
        # API mode
        if symbol == 'USDT' and vs_currency.lower() == 'usd':
            return 1.0  # USDT is pegged to USD
        
        # Check cache
        cache_key = f"{symbol}_{vs_currency}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]
        
        # Try CoinMarketCap first if available
        if self.use_cmc:
            price = self._get_price_from_cmc(symbol, vs_currency)
            if price:
                self._cache_price(cache_key, price)
                return price
        
        # Fallback to CoinGecko
        price = self._get_price_from_coingecko(symbol, vs_currency)
        if price:
            self._cache_price(cache_key, price)
            return price
        
        return None
    
    def _get_price_from_cmc(self, symbol: str, vs_currency: str = 'usd') -> Optional[float]:
        """Get price from CoinMarketCap API."""
        # Check rate limit
        if not self._check_rate_limit():
            print(f"⚠️ CoinMarketCap rate limit approached ({self.api_call_count}/{self.api_call_limit_monthly} calls this month)")
            return None
            
        try:
            coin_id = self.CMC_COIN_MAP.get(symbol)
            if not coin_id:
                return None
            
            url = f"{self.CMC_BASE_URL}/cryptocurrency/quotes/latest"
            params = {
                'id': coin_id,
                'convert': vs_currency.upper()
            }
            
            response = self.session.get(url, params=params, headers=self.cmc_headers, timeout=8)
            response.raise_for_status()
            
            # Track API call
            self._track_api_call()
            
            data = response.json()
            if data.get('status', {}).get('error_code') == 0:
                coin_data = data['data'][str(coin_id)]
                price = coin_data['quote'][vs_currency.upper()]['price']
                return float(price)
            
            return None
        except Exception as e:
            print(f"CoinMarketCap API error for {symbol}: {e}")
            return None
    
    def _get_price_from_coingecko(self, symbol: str, vs_currency: str = 'usd') -> Optional[float]:
        """Get price from CoinGecko API (fallback)."""
        try:
            coin_id = self.COINGECKO_COIN_IDS.get(symbol)
            if not coin_id:
                return None
            
            url = f"{self.COINGECKO_BASE_URL}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': vs_currency
            }
            
            response = self.session.get(url, params=params, timeout=8)
            response.raise_for_status()
            
            data = response.json()
            price = data.get(coin_id, {}).get(vs_currency)
            
            return float(price) if price else None
        except Exception as e:
            print(f"CoinGecko API error for {symbol}: {e}")
            return None
    
    def _cache_price(self, cache_key: str, price: float):
        """Cache a price."""
        self.cache[cache_key] = price
        self.cache_timestamp[cache_key] = datetime.now()
    
    
    def get_multiple_prices(self, symbols: List[str], vs_currency: str = 'usd') -> Dict[str, float]:
        """
        Get prices for multiple cryptocurrencies at once.
        Uses simulator or tries CoinMarketCap first, falls back to CoinGecko.
        
        Args:
            symbols: List of crypto symbols
            vs_currency: Quote currency
        
        Returns:
            Dict mapping symbol to price
        """
        # Simulator mode
        if self.mode == 'simulator':
            return self.simulator.get_multiple_prices(symbols, vs_currency)
        
        # API mode
        prices = {}
        
        # Handle USDT separately
        if 'USDT' in symbols:
            prices['USDT'] = 1.0
        
        other_symbols = [s for s in symbols if s != 'USDT']
        if not other_symbols:
            return prices
        
        # Try CoinMarketCap first if available
        if self.use_cmc:
            cmc_prices = self._get_multiple_prices_from_cmc(other_symbols, vs_currency)
            prices.update(cmc_prices)
            
            # Check if we got all prices
            missing = [s for s in other_symbols if s not in prices]
            if not missing:
                return prices
            other_symbols = missing
        
        # Fallback to CoinGecko for remaining symbols
        gecko_prices = self._get_multiple_prices_from_coingecko(other_symbols, vs_currency)
        prices.update(gecko_prices)
        
        return prices
    
    def _get_multiple_prices_from_cmc(self, symbols: List[str], vs_currency: str = 'usd') -> Dict[str, float]:
        """Get prices for multiple symbols from CoinMarketCap."""
        try:
            coin_ids = [self.CMC_COIN_MAP[s] for s in symbols if s in self.CMC_COIN_MAP]
            if not coin_ids:
                return {}
            
            url = f"{self.CMC_BASE_URL}/cryptocurrency/quotes/latest"
            params = {
                'id': ','.join(map(str, coin_ids)),
                'convert': vs_currency.upper()
            }
            
            response = self.session.get(url, params=params, headers=self.cmc_headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            prices = {}
            
            if data.get('status', {}).get('error_code') == 0:
                for coin_id, coin_data in data['data'].items():
                    for symbol, cid in self.CMC_COIN_MAP.items():
                        if cid == int(coin_id):
                            quote = coin_data['quote'][vs_currency.upper()]
                            price = float(quote['price'])
                            prices[symbol] = price
                            self._cache_price(f"{symbol}_{vs_currency}", price)
                            break
            
            return prices
        except Exception as e:
            print(f"CoinMarketCap batch API error: {e}")
            return {}
    
    def _get_multiple_prices_from_coingecko(self, symbols: List[str], vs_currency: str = 'usd') -> Dict[str, float]:
        """Get prices for multiple symbols from CoinGecko."""
        prices = {}
        
        # Check cache first
        for symbol in symbols:
            cache_key = f"{symbol}_{vs_currency}"
            if self._is_cached(cache_key):
                prices[symbol] = self.cache[cache_key]
        
        # Get uncached symbols
        uncached = [s for s in symbols if s not in prices]
        if not uncached:
            return prices
        
        try:
            coin_ids = [self.COINGECKO_COIN_IDS[s] for s in uncached if s in self.COINGECKO_COIN_IDS]
            if not coin_ids:
                return prices
            
            url = f"{self.COINGECKO_BASE_URL}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': vs_currency
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            for symbol in uncached:
                coin_id = self.COINGECKO_COIN_IDS.get(symbol)
                if coin_id and coin_id in data:
                    price = data[coin_id].get(vs_currency)
                    if price:
                        prices[symbol] = float(price)
                        self._cache_price(f"{symbol}_{vs_currency}", float(price))
            
            return prices
        except Exception as e:
            print(f"CoinGecko batch API error: {e}")
            return prices

            
            if not coin_ids:
                return prices
            
            url = f"{self.BASE_URL}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': vs_currency
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Map results back to symbols
            for symbol in other_symbols:
                coin_id = self.COIN_IDS.get(symbol)
                if coin_id and coin_id in data:
                    price = data[coin_id].get(vs_currency)
                    if price:
                        prices[symbol] = price
                        # Cache individual prices
                        cache_key = f"{symbol}_{vs_currency}"
                        self.cache[cache_key] = price
                        self.cache_timestamp[cache_key] = datetime.now()
            
            return prices
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("⚠️ CoinGecko rate limit hit - using cached prices only")
                # Return cached prices for requested symbols
                for symbol in other_symbols:
                    cache_key = f"{symbol}_{vs_currency}"
                    if cache_key in self.cache:
                        prices[symbol] = self.cache[cache_key]
            else:
                print(f"Error fetching multiple prices: {e}")
            return prices
        except Exception as e:
            print(f"Error fetching multiple prices: {e}")
            # Return cached prices if available
            for symbol in other_symbols:
                cache_key = f"{symbol}_{vs_currency}"
                if cache_key in self.cache:
                    prices[symbol] = self.cache[cache_key]
            return prices
    
    def get_pair_price(self, pair: str) -> Optional[float]:
        """
        Get price for a trading pair (e.g., 'BTC/USDT').
        Uses simulator or API based on mode.
        
        Args:
            pair: Trading pair string
        
        Returns:
            Current price or None
        """
        # Simulator mode
        if self.mode == 'simulator':
            return self.simulator.get_pair_price(pair)
        
        # API mode
        try:
            base, quote = pair.split('/')
            
            # If quote is USDT, get base price in USD
            if quote == 'USDT':
                return self.get_price(base, 'usd')
            
            # Otherwise, calculate the conversion
            base_price = self.get_price(base, 'usd')
            quote_price = self.get_price(quote, 'usd')
            
            if base_price and quote_price:
                return base_price / quote_price
            
            return None
            
        except Exception as e:
            print(f"Error getting pair price for {pair}: {e}")
            return None
    
    def get_24h_change(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Get 24h price change data.
        Calculates from historical data in database to avoid rate limits.
        
        Args:
            symbol: Crypto symbol
        
        Returns:
            Dict with price_change_24h and price_change_percentage_24h
        """
        # Simulator mode
        if self.mode == 'simulator':
            return self.simulator.get_24h_change(symbol)
        
        # Check if we have cached 24h change data
        cache_key = f"{symbol}_24h_change"
        if self._is_cached(cache_key):
            return self.cache[cache_key]
        
        # Try to calculate from historical data in database
        try:
            from utils.historical_data_fetcher import HistoricalDataFetcher
            fetcher = HistoricalDataFetcher()
            historical = fetcher.get_historical_prices(symbol, days=2)
            
            if historical and len(historical) >= 2:
                # Get price from 24h ago and current price
                price_24h_ago = historical[0]['price']
                current_price = self.get_price(symbol)
                
                if current_price and price_24h_ago:
                    price_change = current_price - price_24h_ago
                    price_change_pct = (price_change / price_24h_ago) * 100
                    
                    result = {
                        'price_change_24h': price_change,
                        'price_change_percentage_24h': price_change_pct,
                        'current_price': current_price
                    }
                    
                    # Cache for 5 minutes
                    self.cache[cache_key] = result
                    self.cache_timestamp[cache_key] = datetime.now()
                    
                    return result
        except:
            pass  # Fall through to placeholder
        
        # Fallback: return current price with 0% change
        current_price = self.get_price(symbol)
        if current_price:
            result = {
                'price_change_24h': 0,
                'price_change_percentage_24h': 0,
                'current_price': current_price
            }
            return result
        
        return None
    
    def _get_24h_change_from_cmc(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get 24h change from CoinMarketCap API."""
        # Check rate limit
        if not self._check_rate_limit():
            return None
            
        try:
            coin_id = self.CMC_COIN_MAP.get(symbol)
            if not coin_id:
                return None
            
            url = f"{self.CMC_BASE_URL}/cryptocurrency/quotes/latest"
            params = {
                'id': coin_id,
                'convert': 'USD'
            }
            
            response = self.session.get(url, params=params, headers=self.cmc_headers, timeout=8)
            response.raise_for_status()
            
            # Track API call
            self._track_api_call()
            
            data = response.json()
            if data.get('status', {}).get('error_code') == 0:
                coin_data = data['data'][str(coin_id)]
                quote = coin_data['quote']['USD']
                
                return {
                    'price_change_24h': quote.get('price', 0) * (quote.get('percent_change_24h', 0) / 100),
                    'price_change_percentage_24h': quote.get('percent_change_24h', 0),
                    'current_price': quote.get('price', 0)
                }
            
            return None
        except Exception as e:
            print(f"CoinMarketCap 24h change error for {symbol}: {e}")
            return None
    
    def _get_24h_change_from_coingecko(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get 24h change from CoinGecko API."""
        try:
            coin_id = self.COINGECKO_COIN_IDS.get(symbol)
            if not coin_id:
                return None
            
            url = f"{self.COINGECKO_BASE_URL}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=8)
            response.raise_for_status()
            
            data = response.json()
            market_data = data.get('market_data', {})
            
            return {
                'price_change_24h': market_data.get('price_change_24h', 0),
                'price_change_percentage_24h': market_data.get('price_change_percentage_24h', 0),
                'current_price': market_data.get('current_price', {}).get('usd', 0)
            }
            
        except Exception as e:
            print(f"CoinGecko 24h change error for {symbol}: {e}")
            return None
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if cached value is still valid."""
        if cache_key not in self.cache:
            return False
        
        timestamp = self.cache_timestamp.get(cache_key)
        if not timestamp:
            return False
        
        age = (datetime.now() - timestamp).total_seconds()
        return age < self.cache_duration
    
    def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits for CoinMarketCap Basic Plan.
        - Monthly: 10,000 calls (hard cap)
        - Per-minute: 30 requests
        Returns False if we should stop making API calls.
        """
        from datetime import datetime, timedelta
        from calendar import monthrange
        
        # Check per-minute rate limit first
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Remove calls older than 1 minute
        self.api_calls_per_minute = [
            call_time for call_time in self.api_calls_per_minute 
            if call_time > one_minute_ago
        ]
        
        # Check if we're at the per-minute limit
        if len(self.api_calls_per_minute) >= self.api_call_limit_per_minute:
            print(f"⏱️ CoinMarketCap rate limit: {len(self.api_calls_per_minute)}/30 calls in last minute - throttling")
            return False
        
        # Reset counter if it's a new month
        if self.api_call_reset_date is None:
            # First time - set reset date to end of month
            days_in_month = monthrange(now.year, now.month)[1]
            self.api_call_reset_date = datetime(now.year, now.month, days_in_month, 23, 59, 59)
        elif now > self.api_call_reset_date:
            # New month - reset counter
            self.api_call_count = 0
            days_in_month = monthrange(now.year, now.month)[1]
            self.api_call_reset_date = datetime(now.year, now.month, days_in_month, 23, 59, 59)
            self.rate_limit_warning_shown = False
            print(f"✓ CoinMarketCap API call counter reset for new month")
        
        # Warning at 90% monthly usage
        if self.api_call_count >= self.api_call_limit_monthly * 0.9 and not self.rate_limit_warning_shown:
            print(f"⚠️ WARNING: CoinMarketCap API usage at {self.api_call_count}/{self.api_call_limit_monthly} calls (90%)")
            print(f"   Resets on: {self.api_call_reset_date.strftime('%Y-%m-%d')}")
            self.rate_limit_warning_shown = True
        
        # Stop at 95% monthly limit to prevent hitting hard cap
        if self.api_call_count >= self.api_call_limit_monthly * 0.95:
            print(f"🛑 CoinMarketCap monthly limit protection: {self.api_call_count}/{self.api_call_limit_monthly} calls")
            print(f"   Falling back to CoinGecko API until {self.api_call_reset_date.strftime('%Y-%m-%d')}")
            return False
        
        return True
    
    def _track_api_call(self):
        """Track an API call for rate limiting (both monthly and per-minute)."""
        from datetime import datetime
        
        # Track monthly count
        self.api_call_count += 1
        
        # Track per-minute count
        self.api_calls_per_minute.append(datetime.now())
        
        # Periodic usage reporting
        if self.api_call_count % 100 == 0:
            print(f"📊 CoinMarketCap API usage: {self.api_call_count}/{self.api_call_limit_monthly} calls this month")
        
        # Show current minute rate when approaching limit
        if len(self.api_calls_per_minute) >= 25:
            print(f"⚠️ High request rate: {len(self.api_calls_per_minute)}/30 calls in last minute")
    
    def get_api_usage_stats(self) -> Dict:
        """Get current API usage statistics."""
        remaining = self.api_call_limit_monthly - self.api_call_count
        percentage = (self.api_call_count / self.api_call_limit_monthly) * 100
        
        return {
            'calls_made': self.api_call_count,
            'calls_limit': self.api_call_limit_monthly,
            'calls_remaining': remaining,
            'usage_percentage': percentage,
            'reset_date': self.api_call_reset_date.strftime('%Y-%m-%d') if self.api_call_reset_date else None
        }
    
    def clear_cache(self):
        """Clear the price cache."""
        self.cache = {}
        self.cache_timestamp = {}


# Singleton instance
_price_service = None

def get_price_service() -> PriceService:
    """Get the global price service instance."""
    global _price_service
    if _price_service is None:
        _price_service = PriceService()
    return _price_service
