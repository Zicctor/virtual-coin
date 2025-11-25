"""Configuration management for the application."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Determine the base path for PyInstaller or normal execution
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    base_path = Path(sys._MEIPASS)
else:
    # Running as script
    base_path = Path(__file__).parent

# Load environment variables from .env file
env_path = base_path / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    print(f"⚠️ .env not found at: {env_path}")
    load_dotenv()  # Try to load from current directory as fallback


class Config:
    """Application configuration."""
    
    # Database Configuration (supports both Supabase and Neon/PostgreSQL)
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
    
    # Neon PostgreSQL Configuration (alternative to Supabase)
    NEON_DATABASE_URL = os.getenv('NEON_DATABASE_URL', '')
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'supabase')  # 'supabase' or 'neon'
    
    # FreeCryptoAPI Configuration
    FREECRYPTO_API_KEY = os.getenv('FREECRYPTO_API_KEY', '')
    FREECRYPTO_BASE_URL = 'https://api.freecryptoapi.com/v1'
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_SECRET_FILE = os.path.join(
        os.path.dirname(__file__), 
        'credentials', 
        'client_secret.json'
    )
    GOOGLE_TOKEN_FILE = os.path.join(
        os.path.dirname(__file__), 
        'credentials', 
        'token.pickle'
    )
    
    # Application Settings
    APP_NAME = "CryptoTrade"
    APP_VERSION = "1.0.0"
    
    # Trading Configuration
    DEFAULT_CURRENCIES = ['BTC', 'ETH', 'OP', 'BNB', 'SOL', 'DOGE', 'TRX', 'USDT', 
                          'XRP', 'ADA', 'NEAR', 'LTC', 'BCH', 'XLM', 'LINK', 'MATIC']
    DEFAULT_TRADING_PAIRS = [
        'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT',
        'XRP/USDT', 'ADA/USDT', 'DOGE/USDT', 'TRX/USDT',
        'OP/USDT', 'NEAR/USDT', 'LTC/USDT', 'BCH/USDT',
        'XLM/USDT', 'LINK/USDT', 'MATIC/USDT', 'USDT/USDT'
    ]
    
    # Initial wallet balance for new users (in USDT)
    INITIAL_BALANCE = 10000.00
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        # Check database configuration based on type
        if cls.DATABASE_TYPE == 'neon':
            if not cls.NEON_DATABASE_URL:
                raise ValueError(
                    "Neon database URL not configured. "
                    "Please add NEON_DATABASE_URL to your .env file"
                )
        else:  # supabase
            if not cls.SUPABASE_URL or not cls.SUPABASE_KEY:
                raise ValueError(
                    "Supabase credentials not configured. "
                    "Please create a .env file with SUPABASE_URL and SUPABASE_KEY"
                )
        
        if not os.path.exists(cls.GOOGLE_CLIENT_SECRET_FILE):
            raise FileNotFoundError(
                f"Google OAuth credentials not found at {cls.GOOGLE_CLIENT_SECRET_FILE}. "
                "Please follow SETUP.md instructions."
            )
    
    @classmethod
    def is_configured(cls):
        """Check if database is configured."""
        if cls.DATABASE_TYPE == 'neon':
            return bool(cls.NEON_DATABASE_URL)
        else:
            return bool(cls.SUPABASE_URL and cls.SUPABASE_KEY)
