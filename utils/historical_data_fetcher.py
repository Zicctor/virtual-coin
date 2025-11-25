"""Fetch and store historical cryptocurrency price data from CoinGecko."""
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.database import SupabaseDB


class HistoricalDataFetcher:
    """Fetches historical price data from CoinGecko and stores in Supabase."""
    
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Mapping of symbols to CoinGecko IDs
    COIN_IDS = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'OP': 'optimism',
        'NEAR': 'near',
        'BNB': 'binancecoin',
        'SOL': 'solana',
        'DOGE': 'dogecoin',
        'TRX': 'tron',
        'USDT': 'tether',
        'XRP': 'ripple',
        'ADA': 'cardano',
        'LTC': 'litecoin',
        'BCH': 'bitcoin-cash',
        'XLM': 'stellar',
        'LINK': 'chainlink',
        'MATIC': 'polygon-ecosystem-token'
    }
    
    def __init__(self):
        """Initialize the fetcher."""
        self.db = SupabaseDB()
        self.session = requests.Session()
    
    def fetch_historical_data(self, symbol: str, days: int = 90, retries: int = 3) -> Optional[List[Dict]]:
        """
        Fetch historical price data from CoinGecko with retry logic.
        
        Args:
            symbol: Crypto symbol (BTC, ETH, etc.)
            days: Number of days of history (max 365 for free tier)
            retries: Number of retry attempts on rate limit
        
        Returns:
            List of price data points or None
        """
        coin_id = self.COIN_IDS.get(symbol)
        if not coin_id:
            print(f"Unknown symbol: {symbol}")
            return None
        
        for attempt in range(retries):
            try:
                url = f"{self.COINGECKO_BASE_URL}/coins/{coin_id}/market_chart"
                params = {
                    'vs_currency': 'usd',
                    'days': days,
                    'interval': 'daily'  # daily data points
                }
                
                print(f"Fetching {days} days of historical data for {symbol}... (attempt {attempt + 1}/{retries})")
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                
                # Parse the response
                prices = data.get('prices', [])
                market_caps = data.get('market_caps', [])
                total_volumes = data.get('total_volumes', [])
                
                historical_data = []
                for i in range(len(prices)):
                    timestamp_ms = prices[i][0]
                    price = prices[i][1]
                    market_cap = market_caps[i][1] if i < len(market_caps) else None
                    volume = total_volumes[i][1] if i < len(total_volumes) else None
                    
                    historical_data.append({
                        'symbol': symbol,
                        'timestamp': datetime.fromtimestamp(timestamp_ms / 1000),
                        'price': price,
                        'market_cap': market_cap,
                        'volume_24h': volume
                    })
                
                print(f"✓ Fetched {len(historical_data)} data points for {symbol}")
                return historical_data
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = (attempt + 1) * 10  # 10s, 20s, 30s
                    print(f"⏳ Rate limit hit. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"HTTP Error fetching historical data for {symbol}: {e}")
                    return None
            except Exception as e:
                print(f"Error fetching historical data for {symbol}: {e}")
                return None
        
        print(f"✗ Failed to fetch {symbol} after {retries} attempts")
        return None
    
    def store_historical_data(self, historical_data: List[Dict]) -> bool:
        """
        Store historical data in Supabase.
        
        Args:
            historical_data: List of historical price data
        
        Returns:
            True if successful
        """
        try:
            # Store in batches to avoid timeouts
            batch_size = 100
            for i in range(0, len(historical_data), batch_size):
                batch = historical_data[i:i + batch_size]
                
                # Convert datetime to ISO format for Supabase
                batch_formatted = []
                for item in batch:
                    batch_formatted.append({
                        'symbol': item['symbol'],
                        'timestamp': item['timestamp'].isoformat(),
                        'price': item['price'],
                        'market_cap': item['market_cap'],
                        'volume_24h': item['volume_24h']
                    })
                
                # Upsert (insert or update if exists)
                self.db.client.table('historical_prices').upsert(
                    batch_formatted,
                    on_conflict='symbol,timestamp'
                ).execute()
                
                print(f"  Stored batch {i // batch_size + 1}/{(len(historical_data) + batch_size - 1) // batch_size}")
            
            return True
            
        except Exception as e:
            print(f"Error storing historical data: {e}")
            return False
    
    def update_all_coins(self, days: int = 90):
        """
        Fetch and store historical data for all supported coins.
        Optimized for CoinGecko limits: 10,000 calls/month, 30 calls/minute
        
        Args:
            days: Number of days of history to fetch
        """
        print(f"\n{'='*60}")
        print(f"Starting historical data update for {len(self.COIN_IDS)} coins")
        print(f"Fetching {days} days of data...")
        print(f"CoinGecko Limits: 30 req/min, 10,000 req/month")
        print(f"{'='*60}\n")
        
        success_count = 0
        fail_count = 0
        
        for symbol in self.COIN_IDS.keys():
            # Fetch data
            historical_data = self.fetch_historical_data(symbol, days)
            
            if historical_data:
                # Store data
                if self.store_historical_data(historical_data):
                    success_count += 1
                    print(f"✓ {symbol}: Successfully updated\n")
                else:
                    fail_count += 1
                    print(f"✗ {symbol}: Failed to store data\n")
            else:
                fail_count += 1
                print(f"✗ {symbol}: Failed to fetch data\n")
            
            # Rate limiting - respect 30 req/min = 1 request per 2 seconds
            # Using 10 seconds to be very safe for free tier without API key
            print(f"⏳ Waiting 10 seconds before next request...")
            time.sleep(10)
        
        print(f"\n{'='*60}")
        print(f"Update Complete!")
        print(f"Success: {success_count}/{len(self.COIN_IDS)}")
        print(f"Failed: {fail_count}/{len(self.COIN_IDS)}")
        print(f"API Calls Used: {len(self.COIN_IDS)} (Monthly budget: 10,000)")
        print(f"{'='*60}\n")
    
    def get_historical_prices(self, symbol: str, days: int = 30) -> Optional[List[Dict]]:
        """
        Get historical prices from database.
        
        Args:
            symbol: Crypto symbol
            days: Number of days to retrieve
        
        Returns:
            List of historical price data
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            result = self.db.client.table('historical_prices').select('*').eq(
                'symbol', symbol
            ).gte('timestamp', cutoff_date).order('timestamp', desc=False).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error retrieving historical prices for {symbol}: {e}")
            return None


def get_historical_data(coin_id: str, start_date: datetime, end_date: datetime) -> Optional[List[Dict]]:
    """
    Get historical price data from Supabase database.
    
    Args:
        coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
    
    Returns:
        List of historical price records with 'timestamp' and 'price' fields
    """
    try:
        # Reverse map coin_id to symbol
        coin_id_to_symbol = {v: k for k, v in HistoricalDataFetcher.COIN_IDS.items()}
        symbol = coin_id_to_symbol.get(coin_id)
        
        if not symbol:
            print(f"Unknown coin_id: {coin_id}")
            return None
        
        db = SupabaseDB()
        
        result = db.client.table('historical_prices').select('timestamp, price').eq(
            'symbol', symbol
        ).gte('timestamp', start_date.isoformat()).lte(
            'timestamp', end_date.isoformat()
        ).order('timestamp', desc=False).execute()
        
        if not result.data:
            return None
        
        # Convert timestamp strings to datetime objects
        for record in result.data:
            if isinstance(record['timestamp'], str):
                record['timestamp'] = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
        
        return result.data
        
    except Exception as e:
        print(f"Error getting historical data for {coin_id}: {e}")
        return None


def main():
    """Main function to run the historical data update."""
    fetcher = HistoricalDataFetcher()
    
    # Fetch 90 days of historical data for all coins
    fetcher.update_all_coins(days=90)


if __name__ == "__main__":
    main()
