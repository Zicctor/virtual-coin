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

- **Users** - User authentication (google_id, email, name)
- **Wallets** - User balances per currency (balance, locked_balance)
- **Orders** - Trading orders (market/limit/stop-limit, buy/sell)
- **Transactions** - Complete trade history with fees

## Project Structure

```
pyqt_crypto_app/
├── main.py                 # Application entry point
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Your credentials (create this)
├── SETUP.md               # Google OAuth setup guide
├── SUPABASE_SETUP.md      # Supabase database setup guide
├── README.md              # This file
├── test_database.py       # Database test suite
├── auth/
│   ├── __init__.py
│   └── google_auth.py     # Google OAuth manager with Supabase sync
├── ui/
│   ├── __init__.py
│   └── login_window.py    # Login window UI
├── utils/
│   ├── __init__.py
│   └── database.py        # Supabase database operations
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

- Python 3.8 or higher
- Google Cloud account (for OAuth)
- Supabase account (free tier available)

### 1. Set Up Supabase Database

Follow the detailed guide in [SUPABASE_SETUP.md](SUPABASE_SETUP.md):
- Create Supabase project
- Run SQL scripts to create tables (Users, Wallets, Orders, Transactions)
- Get your project URL and service role key

### 2. Set Up Google OAuth

Follow the instructions in [SETUP.md](SETUP.md):
- Create Google Cloud project
- Enable Google+ API
- Create OAuth 2.0 credentials (Desktop app)
- Download `client_secret.json`

### 3. Configure Environment

```powershell
cd pyqt_crypto_app

# Copy environment template
Copy-Item .env.example .env

# Edit .env file and add your credentials
notepad .env
```

Add your Supabase credentials:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key-here
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
python test_database.py
```

This will:
- ✅ Verify Supabase connection
- ✅ Test user creation
- ✅ Test wallet initialization
- ✅ Test order/transaction creation

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

- Python 3.8+
- PyQt6 6.6.0+
- Google OAuth 2.0 credentials
- Supabase account and database

See `requirements.txt` for complete list of dependencies.

## Configuration

### Environment Variables (.env)

```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_service_role_key

# No need to configure Google OAuth in .env
# It uses credentials/client_secret.json
```

### Application Settings (config.py)

- `INITIAL_BALANCE`: $10,000 USDT for new users
- `DEFAULT_CURRENCIES`: BTC, ETH, BNB, USDT, XRP, ADA, SOL, DOT
- `DEFAULT_TRADING_PAIRS`: BTC/USDT, ETH/USDT, etc.

## Database Operations

The `utils/database.py` module provides:

**User Operations:**
- `create_user()` - Create new user with Google OAuth
- `get_user_by_google_id()` - Retrieve user
- `get_user_by_email()` - Find user by email

**Wallet Operations:**
- `initialize_user_wallets()` - Set up default wallets
- `get_user_wallets()` - Get all balances
- `get_wallet_balance()` - Get specific currency balance
- `update_wallet_balance()` - Update balance

**Trading Operations:**
- `create_order()` - Place buy/sell order
- `execute_market_order()` - Execute trade and update balances
- `get_user_orders()` - Get order history
- `cancel_order()` - Cancel pending order

**Transaction History:**
- `create_transaction()` - Record trade
- `get_user_transactions()` - Get trade history
- `get_transactions_by_pair()` - Filter by trading pair

**Portfolio:**
- `get_portfolio_value()` - Calculate total portfolio value in USDT

## Development Status

✅ **Completed:**
- Google OAuth authentication
- Supabase database integration
- User management system
- Wallet initialization
- Order and transaction tracking
- Login window with Binance-style UI
- Database test suite
- Complete documentation

🚧 **In Progress:**
- Main trading interface
- Real-time crypto price API integration
- Trading UI components
- Portfolio dashboard
- Chart visualization

## Testing

Run the database test suite:

```powershell
python test_database.py
```

This comprehensive test will:
1. Verify Supabase connection
2. Create a test user
3. Initialize wallets
4. Test balance updates
5. Create sample orders
6. Create sample transactions
7. Verify all CRUD operations

## Architecture

```
┌─────────────────┐
│   PyQt6 UI      │  Login, Trading, Portfolio
└────────┬────────┘
         │
┌────────▼────────┐
│  Google OAuth   │  Authentication & User Info
└────────┬────────┘
         │
┌────────▼────────┐
│  Supabase DB    │  Users, Wallets, Orders, Transactions
└────────┬────────┘
         │
┌────────▼────────┐
│  PostgreSQL     │  Cloud Database
└─────────────────┘
```

## Security

### What's Protected (.gitignore)

- ✅ `.env` (Supabase credentials)
- ✅ `credentials/client_secret.json` (Google OAuth)
- ✅ `credentials/token.pickle` (Auth tokens)
- ✅ `__pycache__/` (Python cache)

### Security Best Practices

⚠️ **Never commit sensitive files!**
- Use `.env` for all API keys
- Use `service_role` key (not `anon` key) for Supabase
- Keep `client_secret.json` private
- Enable Row Level Security (RLS) on Supabase for production

## License

Private project - All rights reserved

## Troubleshooting

**"Supabase credentials not configured"**
- Create `.env` file in `pyqt_crypto_app/` folder
- Add `SUPABASE_URL` and `SUPABASE_KEY`
- See `.env.example` for template

**"Client secret file not found"**
- Download `client_secret.json` from Google Cloud Console
- Place in `credentials/` folder
- See `SETUP.md` for instructions

**Database connection fails**
- Run `python test_database.py` to diagnose
- Check Supabase project is active (not paused)
- Verify credentials in `.env` are correct
- Check internet connection

**Icons not showing**
- Icons downloaded automatically on first setup
- See `assets/ICONS_GUIDE.md` for manual setup

## Documentation

- **[SETUP.md](SETUP.md)** - Google OAuth setup guide
- **[SUPABASE_SETUP.md](SUPABASE_SETUP.md)** - Complete database setup
- **[assets/ICONS_GUIDE.md](assets/ICONS_GUIDE.md)** - Icon customization
- **[.env.example](.env.example)** - Environment variables template

## Support

For issues:
1. Check documentation files above
2. Run `python test_database.py` for database diagnostics
3. Verify `.env` configuration
4. Check Supabase dashboard for table structure
