# PyQt6 Crypto Trading App - DuckyTrading

A desktop cryptocurrency trading application built with PyQt6, featuring Google OAuth authentication, Neon PostgreSQL database, and real-time crypto data from CoinGecko.

## Features

- 🔐 **Google OAuth Authentication**: Secure login with Google accounts
- 💾 **Neon PostgreSQL Database**: Cloud-based database shared across all users
- 📊 **Real-time Crypto Prices**: Live cryptocurrency market data from CoinGecko
- 💰 **Virtual Trading**: Buy and sell crypto with virtual currency ($10,000 USDT starting balance)
- 📈 **Portfolio Tracking**: Monitor your holdings and performance
- 🎨 **Binance-Style UI**: Professional dark theme interface
- 📜 **Order History**: Track all your trades and transactions
- 💼 **Multi-Currency Wallets**: Support for 16+ cryptocurrencies
- 🎁 **Daily Login Bonus**: Claim 100 USDT every 24 hours
- 🏆 **Leaderboard**: Compete with other traders
- 🤝 **P2P Trading**: Create and accept trade offers with other users
- 🔄 **Auto-Updates**: Automatic update checker notifies you of new versions

## Distribution & Updates

**For Developers:**
- See [GITHUB_RELEASES_GUIDE.md](GITHUB_RELEASES_GUIDE.md) for how to create and publish updates
- Version is tracked in `version.py`
- Build with `python package_app.py`

**For Users:**
- App automatically checks for updates on startup
- Download latest version from GitHub Releases
- Get `.env` file from developer (contains database connection)

## Database Schema

The app uses **Neon PostgreSQL** with the following tables:

- **Users** - User authentication (google_id, email, name, last_login_bonus)
- **Wallets** - User balances per currency (balance, locked_balance)
- **PortfolioHistory** - Historical portfolio value tracking
- **DailyLogins** - Daily login bonus tracking
- **TradeOffers** - P2P trading offers
- **UserTransactions** - Complete trade history with fees
- **P2PTradeTransactions** - P2P trade execution history

## Project Structure

```
pyqt_crypto_app/
├── main.py                 # Application entry point
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── .env                    # Your credentials (NOT in git)
├── version.py              # App version tracking
├── package_app.py          # PyInstaller build script
├── GITHUB_RELEASES_GUIDE.md # Distribution guide
├── README.md              # This file
├── reset_neon_database.sql # Database reset script
├── auth/
│   ├── __init__.py
│   └── google_auth.py     # Google OAuth manager
├── ui/
│   ├── __init__.py
│   ├── login_window.py    # Login window UI
│   ├── trading_window.py  # Main trading interface
│   ├── leaderboard_window.py # Leaderboard UI
│   ├── chart_widget.py    # Chart visualization
│   └── web_chart_widget.py # CoinGecko charts
├── utils/
│   ├── __init__.py
│   ├── neon_database.py   # Neon PostgreSQL operations
│   ├── price_service.py   # CoinGecko API integration
│   ├── update_checker.py  # GitHub update checker
│   └── freecrypto_service.py # Free crypto faucet
├── assets/
│   ├── icons/             # App icons
│   │   ├── app_icon.png
│   │   ├── google_icon.png
│   │   └── bitcoin_icon.png
│   └── ICONS_GUIDE.md     # Icon usage guide
├── credentials/           # OAuth credentials (not in git)
│   ├── client_secret.json # From Google Cloud Console
│   └── token.pickle       # Auto-generated auth token
└── .gitignore

```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Google Cloud account (for OAuth)
- Neon PostgreSQL account (free tier available)

### 1. Set Up Neon Database

Create a Neon PostgreSQL database:
- Sign up at https://neon.tech
- Create a new project
- Run `reset_neon_database.sql` in Neon SQL console to create all tables
- Copy the connection string from dashboard

### 2. Set Up Google OAuth

- Create Google Cloud project at https://console.cloud.google.com
- Enable Google+ API
- Create OAuth 2.0 credentials (Desktop app type)
- Download `client_secret.json` and place in `credentials/` folder

### 3. Configure Environment

```powershell
cd pyqt_crypto_app

# Create .env file
notepad .env
```

Add your Neon database connection:
```env
NEON_DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
USE_SIMULATOR=false
COINGECKO_API_KEY=your-api-key-here
```

Place Google credentials:
```
credentials/client_secret.json  # Download from Google Cloud Console
```

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 5. Test Database Connection

```powershell
python check_database.py
```

This will:
- ✅ Verify Neon PostgreSQL connection
- ✅ List all database tables
- ✅ Show table structures

### 6. Run the Application

```powershell
python main.py
```

On first run:
1. Login window appears
2. Click "Sign in with Google"
3. Browser opens for authentication
4. Grant permissions
5. Your account is created automatically with $10,000 USDT!

## Requirements

- Python 3.11+
- PyQt6 6.6.0+
- Google OAuth 2.0 credentials
- Neon PostgreSQL database
- CoinGecko API key (free tier)

See `requirements.txt` for complete list of dependencies.

## Configuration

### Environment Variables (.env)

```env
# Neon PostgreSQL
NEON_DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require

# Price API
USE_SIMULATOR=false
COINGECKO_API_KEY=your-api-key-here

# Google OAuth uses credentials/client_secret.json
```

### Application Settings (config.py)

- `INITIAL_BALANCE`: $10,000 USDT for new users
- `DEFAULT_CURRENCIES`: BTC, ETH, BNB, USDT, XRP, ADA, SOL, DOT
- `DEFAULT_TRADING_PAIRS`: BTC/USDT, ETH/USDT, etc.

## Database Operations

The `utils/neon_database.py` module provides:

**User Operations:**
- `create_user()` - Create new user with Google OAuth
- `get_user_by_google_id()` - Retrieve user
- `claim_daily_bonus()` - Award 100 USDT daily bonus

**Wallet Operations:**
- `initialize_user_wallets()` - Set up default wallets
- `get_user_wallets()` - Get all balances
- `update_balance()` - Update wallet balance

**Trading Operations:**
- `execute_buy()` - Execute buy order and update balances
- `execute_sell()` - Execute sell order and update balances
- `get_user_transactions()` - Get trade history

**P2P Trading:**
- `create_trade_offer()` - Create P2P trade offer
- `accept_trade_offer()` - Accept and execute P2P trade
- `get_active_trade_offers()` - Get available trade offers

**Leaderboard:**
- `get_leaderboard()` - Get top traders by portfolio value

## Development Status

✅ **Completed:**
- Google OAuth authentication
- Neon PostgreSQL database integration
- User management system
- Wallet initialization and tracking
- Login window with Binance-style UI
- Main trading interface (buy/sell)
- Real-time crypto price API (CoinGecko)
- Portfolio dashboard with charts
- Daily login bonus system
- Leaderboard with rankings
- P2P trading system
- GitHub releases and auto-updates
- PyInstaller packaging for distribution
- Complete documentation

## Testing

Run database checks:

```powershell
python check_database.py
```

Test API connections:

```powershell
python test_api.py
```

Test update checker:

```powershell
python test_update_checker.py
```

## Architecture

```
┌─────────────────┐
│   PyQt6 UI      │  Login, Trading, Portfolio, Leaderboard
└────────┬────────┘
         │
┌────────▼────────┐
│  Google OAuth   │  Authentication & User Info
└────────┬────────┘
         │
┌────────▼────────┐
│   Neon DB       │  Users, Wallets, Transactions, P2P Trades
└─────────────────┘
         +
┌─────────────────┐
│  CoinGecko API  │  Real-time crypto prices
└─────────────────┘
         +
┌─────────────────┐
│  GitHub API     │  Auto-update checker
└─────────────────┘
```

## Security

### What's Protected (.gitignore)

- ✅ `.env` (Neon database connection string + API keys)
- ✅ `credentials/client_secret.json` (Google OAuth credentials)
- ✅ `credentials/token.pickle` (User-specific auth tokens)
- ✅ `__pycache__/` (Python cache)
- ✅ `build/` and `dist/` (PyInstaller output)

### Security Best Practices

⚠️ **Never commit sensitive files!**
- Use `.env` for all API keys and database URLs
- Keep `client_secret.json` private (don't push to GitHub)
- Never package `token.pickle` (user-specific, created locally)
- Share `.env` and `client_secret.json` separately with users (encrypted)

## License

Private project - All rights reserved

## Troubleshooting

**"Database credentials not configured"**
- Create `.env` file in `pyqt_crypto_app/` folder
- Add `NEON_DATABASE_URL` with full connection string
- Get connection string from Neon dashboard

**"Client secret file not found"**
- Download `client_secret.json` from Google Cloud Console
- Place in `credentials/` folder
- OAuth app type must be "Desktop app"

**Database connection fails**
- Run `python check_database.py` to diagnose
- Check Neon project is active (not paused after 5 days inactivity)
- Verify `NEON_DATABASE_URL` in `.env` is correct
- Check internet connection
- Ensure connection string includes `?sslmode=require`

**Prices not updating**
- Check `COINGECKO_API_KEY` in `.env`
- CoinGecko free tier: 10,000 calls/month
- App uses 1 call/minute = ~1,440 calls/month (well under limit)
- Set `USE_SIMULATOR=true` to test without API

**Icons not showing**
- Icons downloaded automatically on first setup
- See `assets/ICONS_GUIDE.md` for manual setup

## Documentation

- **[GITHUB_RELEASES_GUIDE.md](GITHUB_RELEASES_GUIDE.md)** - How to create releases and distribute updates
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - PyInstaller packaging guide
- **[HISTORICAL_DATA_README.md](HISTORICAL_DATA_README.md)** - Historical price data setup
- **[assets/ICONS_GUIDE.md](assets/ICONS_GUIDE.md)** - Icon customization
- **[reset_neon_database.sql](reset_neon_database.sql)** - Database schema

## Building for Distribution

```powershell
# Install dependencies
pip install -r requirements.txt

# Build executable
python package_app.py

# Output in: dist/DuckyTrading/
```

See [GITHUB_RELEASES_GUIDE.md](GITHUB_RELEASES_GUIDE.md) for publishing releases.

## Support

For issues:
1. Check documentation files above
2. Run `python check_database.py` for database diagnostics
3. Verify `.env` configuration (NEON_DATABASE_URL, COINGECKO_API_KEY)
4. Check Neon console for table structure
