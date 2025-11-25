"""
Comprehensive test suite for DuckyTrading Application
Tests all major features before packaging to EXE
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test results tracking
test_results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_pass(test_name):
    """Mark test as passed."""
    test_results['passed'].append(test_name)
    print(f"✅ PASS: {test_name}")

def test_fail(test_name, error):
    """Mark test as failed."""
    test_results['failed'].append((test_name, str(error)))
    print(f"❌ FAIL: {test_name}")
    print(f"   Error: {error}")

def test_warn(test_name, message):
    """Mark test as warning."""
    test_results['warnings'].append((test_name, message))
    print(f"⚠️  WARN: {test_name}")
    print(f"   {message}")

def test_environment():
    """Test 1: Environment Configuration"""
    print_section("TEST 1: Environment Configuration")
    
    try:
        # Check .env file exists
        if not os.path.exists('.env'):
            test_fail("Environment file", ".env file not found")
            return
        
        # Check required environment variables
        required_vars = ['DATABASE_TYPE', 'NEON_DATABASE_URL']
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            test_fail("Environment variables", f"Missing: {', '.join(missing)}")
        else:
            test_pass("Environment variables")
        
        # Check database type
        db_type = os.getenv('DATABASE_TYPE')
        if db_type not in ['neon', 'supabase']:
            test_warn("Database type", f"Unknown DATABASE_TYPE: {db_type}")
        else:
            test_pass("Database type configuration")
            
    except Exception as e:
        test_fail("Environment setup", e)

def test_dependencies():
    """Test 2: Required Dependencies"""
    print_section("TEST 2: Required Dependencies")
    
    required_packages = [
        ('PyQt6', 'PyQt6'),
        ('psycopg2', 'psycopg2'),
        ('python-dotenv', 'dotenv'),
        ('requests', 'requests'),
        ('google-auth', 'google.auth'),
        ('google-auth-oauthlib', 'google_auth_oauthlib'),
        ('google-api-python-client', 'googleapiclient'),
        ('python-dateutil', 'dateutil')
    ]
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            test_pass(f"Package: {package_name}")
        except ImportError as e:
            test_fail(f"Package: {package_name}", f"Not installed - run: pip install {package_name}")

def test_config():
    """Test 3: Application Configuration"""
    print_section("TEST 3: Application Configuration")
    
    try:
        from config import Config
        
        # Check Config class can be instantiated
        if Config.is_configured():
            test_pass("Config class initialization")
        else:
            test_fail("Config class", "is_configured() returned False")
        
        # Check default currencies
        if hasattr(Config, 'DEFAULT_CURRENCIES') and len(Config.DEFAULT_CURRENCIES) > 0:
            test_pass(f"Default currencies ({len(Config.DEFAULT_CURRENCIES)} coins)")
            print(f"   Supported: {', '.join(Config.DEFAULT_CURRENCIES)}")
        else:
            test_fail("Default currencies", "No currencies configured")
        
        # Check trading pairs
        if hasattr(Config, 'DEFAULT_TRADING_PAIRS') and len(Config.DEFAULT_TRADING_PAIRS) > 0:
            test_pass(f"Trading pairs ({len(Config.DEFAULT_TRADING_PAIRS)} pairs)")
        else:
            test_fail("Trading pairs", "No trading pairs configured")
        
        # Check initial balance
        if hasattr(Config, 'INITIAL_BALANCE') and Config.INITIAL_BALANCE > 0:
            test_pass(f"Initial balance (${Config.INITIAL_BALANCE:,.2f})")
        else:
            test_warn("Initial balance", "INITIAL_BALANCE not set or is 0")
            
    except Exception as e:
        test_fail("Config module", e)

def test_database_connection():
    """Test 4: Database Connection"""
    print_section("TEST 4: Database Connection")
    
    try:
        from utils.db_factory import get_database
        
        db = get_database()
        test_pass("Database factory")
        
        # Test connection with a simple query
        result = db._execute('SELECT 1 as test')
        if result and len(result) > 0:
            test_pass("Database connection and query")
        else:
            test_fail("Database query", "Query returned no results")
        
        # Check tables exist
        tables = ['Users', 'Wallets', 'Transactions', 'Orders', 'TradeOffers', 'P2PTradeTransactions']
        for table in tables:
            try:
                db._execute(f'SELECT COUNT(*) FROM "{table}"')
                test_pass(f"Table exists: {table}")
            except Exception as e:
                test_fail(f"Table: {table}", str(e))
                
    except Exception as e:
        test_fail("Database connection", e)

def test_price_service():
    """Test 5: Price Service"""
    print_section("TEST 5: Price Service")
    
    try:
        from utils.price_service import get_price_service
        
        price_service = get_price_service()
        test_pass("Price service initialization")
        
        # Test getting a single price
        btc_price = price_service.get_pair_price('BTC/USDT')
        if btc_price and btc_price > 0:
            test_pass(f"BTC price fetch (${btc_price:,.2f})")
        else:
            test_warn("BTC price", "Could not fetch BTC/USDT price")
        
        # Test getting multiple prices
        symbols = ['BTC', 'ETH', 'BNB']
        prices = price_service.get_multiple_prices(symbols)
        if prices and len(prices) > 0:
            test_pass(f"Multiple prices fetch ({len(prices)} coins)")
            for symbol, price in list(prices.items())[:3]:
                print(f"   {symbol}: ${price:,.2f}")
        else:
            test_warn("Multiple prices", "Could not fetch multiple prices")
            
    except Exception as e:
        test_fail("Price service", e)

def test_authentication():
    """Test 6: Authentication System"""
    print_section("TEST 6: Authentication System")
    
    try:
        from auth.google_auth import GoogleAuthManager
        from pathlib import Path
        
        # Check credentials directory
        creds_dir = Path('credentials')
        if creds_dir.exists():
            test_pass("Credentials directory exists")
        else:
            test_fail("Credentials directory", "credentials/ folder not found")
            return
        
        # Check client secret file
        client_secret = creds_dir / 'client_secret.json'
        if client_secret.exists():
            test_pass("Google OAuth client_secret.json exists")
        else:
            test_warn("OAuth credentials", "client_secret.json not found - OAuth login will fail")
        
        # Check GoogleAuthManager can be instantiated
        auth_manager = GoogleAuthManager()
        test_pass("GoogleAuthManager initialization")
        
    except Exception as e:
        test_fail("Authentication system", e)

def test_ui_components():
    """Test 7: UI Components"""
    print_section("TEST 7: UI Components")
    
    try:
        # Test importing UI modules
        from ui.login_window import LoginWindow
        test_pass("LoginWindow module")
        
        from ui.trading_window import TradingWindow
        test_pass("TradingWindow module")
        
        from ui.leaderboard_window import LeaderboardWindow
        test_pass("LeaderboardWindow module")
        
        from ui.web_chart_widget import CoinGeckoChartWidget
        test_pass("CoinGeckoChartWidget module")
        
    except Exception as e:
        test_fail("UI components", e)

def test_assets():
    """Test 8: Asset Files"""
    print_section("TEST 8: Asset Files")
    
    try:
        from config import Config
        
        icons_dir = Path('assets/icons')
        if not icons_dir.exists():
            test_fail("Icons directory", "assets/icons/ not found")
            return
        
        test_pass("Icons directory exists")
        
        # Check for coin icons
        required_icons = [f"{coin.lower()}.png" for coin in Config.DEFAULT_CURRENCIES]
        missing_icons = []
        
        for icon in required_icons:
            if not (icons_dir / icon).exists():
                missing_icons.append(icon)
        
        if missing_icons:
            test_warn("Coin icons", f"Missing: {', '.join(missing_icons[:5])}" + 
                     (f" and {len(missing_icons) - 5} more" if len(missing_icons) > 5 else ""))
        else:
            test_pass(f"All coin icons present ({len(required_icons)} icons)")
        
        # Check for app icon
        if (icons_dir / 'app_icon.png').exists():
            test_pass("Application icon exists")
        else:
            test_warn("App icon", "app_icon.png not found")
            
    except Exception as e:
        test_fail("Asset files", e)

def test_database_operations():
    """Test 9: Database Operations"""
    print_section("TEST 9: Database Operations")
    
    try:
        from utils.db_factory import get_database
        
        db = get_database()
        
        # Test getting wallets (without creating test user)
        try:
            # Just test that the method exists and works
            wallets = db.get_user_wallets(999999)  # Non-existent user
            test_pass("get_user_wallets method")
        except Exception as e:
            if "does not exist" not in str(e).lower():
                test_fail("get_user_wallets", e)
            else:
                test_pass("get_user_wallets method (tested with non-existent user)")
        
        # Test price calculation methods
        test_prices = {'BTC/USDT': 98000, 'ETH/USDT': 3500}
        portfolio = db.get_portfolio_value(999999, test_prices)
        if portfolio and 'total_value' in portfolio:
            test_pass("get_portfolio_value method")
        else:
            test_fail("get_portfolio_value", "Invalid return format")
        
        # Test leaderboard
        leaderboard = db.get_leaderboard(test_prices, limit=10)
        if isinstance(leaderboard, list):
            test_pass(f"get_leaderboard method ({len(leaderboard)} users)")
        else:
            test_fail("get_leaderboard", "Invalid return type")
            
    except Exception as e:
        test_fail("Database operations", e)

def test_scripts():
    """Test 10: Utility Scripts"""
    print_section("TEST 10: Utility Scripts")
    
    scripts = [
        ('main.py', 'Main application entry'),
        ('reset_database.py', 'Database reset utility'),
        ('check_database.py', 'Database checker'),
        ('fix_p2p_columns.py', 'P2P migration script')
    ]
    
    for script, description in scripts:
        if os.path.exists(script):
            test_pass(f"{script} - {description}")
        else:
            test_warn(f"{script}", f"Not found - {description}")

def print_summary():
    """Print test summary."""
    print_section("TEST SUMMARY")
    
    total_tests = len(test_results['passed']) + len(test_results['failed']) + len(test_results['warnings'])
    
    print(f"\n📊 Total Tests Run: {total_tests}")
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    
    if test_results['failed']:
        print("\n❌ FAILED TESTS:")
        for test_name, error in test_results['failed']:
            print(f"   • {test_name}")
            print(f"     {error}")
    
    if test_results['warnings']:
        print("\n⚠️  WARNINGS:")
        for test_name, message in test_results['warnings']:
            print(f"   • {test_name}")
            print(f"     {message}")
    
    print("\n" + "=" * 80)
    
    if len(test_results['failed']) == 0:
        print("🎉 ALL CRITICAL TESTS PASSED!")
        print("✅ Application is ready for packaging to EXE")
        if test_results['warnings']:
            print(f"⚠️  Note: {len(test_results['warnings'])} non-critical warnings")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("🔧 Please fix the issues above before packaging")
        return False

def main():
    """Run all tests."""
    print("=" * 80)
    print("  🧪 DuckyTrading - Master Test Suite")
    print("  Testing all components before EXE packaging")
    print("=" * 80)
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Run all tests
    test_environment()
    test_dependencies()
    test_config()
    test_database_connection()
    test_price_service()
    test_authentication()
    test_ui_components()
    test_assets()
    test_database_operations()
    test_scripts()
    
    # Print summary
    success = print_summary()
    
    print("\n" + "=" * 80)
    if success:
        print("📦 NEXT STEPS:")
        print("   1. Review any warnings above")
        print("   2. Run: pip install pyinstaller")
        print("   3. Run: python package_app.py")
        print("   4. Find your EXE in dist/DuckyTrading/")
    else:
        print("🔧 FIX REQUIRED:")
        print("   1. Address all failed tests above")
        print("   2. Re-run this test: python master_test.py")
        print("   3. Once all tests pass, proceed with packaging")
    print("=" * 80)
    
    return 0 if success else 1

if __name__ == '__main__':
    exit_code = main()
    input("\nPress Enter to exit...")
    sys.exit(exit_code)
