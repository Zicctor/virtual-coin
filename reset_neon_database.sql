-- ============================================================================
-- Neon Database Reset Script
-- WARNING: This will DELETE ALL DATA in your database!
-- Use this to completely reset your DuckyTrading database to a clean state
-- ============================================================================

-- Drop all existing tables (in correct order due to foreign keys)
DROP TABLE IF EXISTS "P2PTradeTransactions" CASCADE;
DROP TABLE IF EXISTS "UserTransactions" CASCADE;
DROP TABLE IF EXISTS "TradeOffers" CASCADE;
DROP TABLE IF EXISTS "DailyLogins" CASCADE;
DROP TABLE IF EXISTS "PortfolioHistory" CASCADE;
DROP TABLE IF EXISTS "Wallets" CASCADE;
DROP TABLE IF EXISTS "Users" CASCADE;

-- ============================================================================
-- CREATE TABLES
-- ============================================================================

-- Users table
CREATE TABLE "Users" (
    user_id SERIAL PRIMARY KEY,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    profile_picture TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_bonus TIMESTAMP
);

-- Wallets table
CREATE TABLE "Wallets" (
    wallet_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "Users"(user_id) ON DELETE CASCADE,
    currency VARCHAR(10) NOT NULL,
    balance DECIMAL(20, 8) DEFAULT 0,
    locked_balance DECIMAL(20, 8) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, currency)
);

-- Portfolio History table
CREATE TABLE "PortfolioHistory" (
    history_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "Users"(user_id) ON DELETE CASCADE,
    total_value DECIMAL(20, 2) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily Logins table (for login bonuses)
CREATE TABLE "DailyLogins" (
    login_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "Users"(user_id) ON DELETE CASCADE,
    login_date DATE NOT NULL,
    bonus_amount DECIMAL(20, 2) DEFAULT 0,
    UNIQUE(user_id, login_date)
);

-- Trade Offers table (P2P Trading)
CREATE TABLE "TradeOffers" (
    offer_id SERIAL PRIMARY KEY,
    creator_id INTEGER REFERENCES "Users"(user_id) ON DELETE CASCADE,
    offering_currency VARCHAR(10) NOT NULL,
    offering_amount DECIMAL(20, 8) NOT NULL,
    requesting_currency VARCHAR(10) NOT NULL,
    requesting_amount DECIMAL(20, 8) NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    accepted_by INTEGER REFERENCES "Users"(user_id) ON DELETE SET NULL
);

-- User Transactions table (Transaction History)
CREATE TABLE "UserTransactions" (
    transaction_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "Users"(user_id) ON DELETE CASCADE,
    transaction_type VARCHAR(20) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8),
    total_cost DECIMAL(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- P2P Trade Transactions table (Completed P2P Trades)
CREATE TABLE "P2PTradeTransactions" (
    trade_id SERIAL PRIMARY KEY,
    offer_id INTEGER REFERENCES "TradeOffers"(offer_id) ON DELETE CASCADE,
    acceptor_id INTEGER REFERENCES "Users"(user_id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CREATE INDEXES for performance
-- ============================================================================

CREATE INDEX idx_wallets_user_id ON "Wallets"(user_id);
CREATE INDEX idx_wallets_currency ON "Wallets"(currency);
CREATE INDEX idx_portfolio_user_id ON "PortfolioHistory"(user_id);
CREATE INDEX idx_portfolio_recorded_at ON "PortfolioHistory"(recorded_at);
CREATE INDEX idx_daily_logins_user_id ON "DailyLogins"(user_id);
CREATE INDEX idx_daily_logins_date ON "DailyLogins"(login_date);
CREATE INDEX idx_trade_offers_creator_id ON "TradeOffers"(creator_id);
CREATE INDEX idx_trade_offers_status ON "TradeOffers"(status);
CREATE INDEX idx_transactions_user_id ON "UserTransactions"(user_id);
CREATE INDEX idx_transactions_type ON "UserTransactions"(transaction_type);
CREATE INDEX idx_transactions_created_at ON "UserTransactions"(created_at);
CREATE INDEX idx_p2p_trades_offer_id ON "P2PTradeTransactions"(offer_id);
CREATE INDEX idx_p2p_trades_acceptor_id ON "P2PTradeTransactions"(acceptor_id);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Show all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Show row counts (should all be 0)
SELECT 
    'Users' as table_name, COUNT(*) as row_count FROM "Users"
UNION ALL
SELECT 'Wallets', COUNT(*) FROM "Wallets"
UNION ALL
SELECT 'PortfolioHistory', COUNT(*) FROM "PortfolioHistory"
UNION ALL
SELECT 'DailyLogins', COUNT(*) FROM "DailyLogins"
UNION ALL
SELECT 'TradeOffers', COUNT(*) FROM "TradeOffers"
UNION ALL
SELECT 'UserTransactions', COUNT(*) FROM "UserTransactions"
UNION ALL
SELECT 'P2PTradeTransactions', COUNT(*) FROM "P2PTradeTransactions";

-- ============================================================================
-- RESET COMPLETE
-- ============================================================================
-- All tables have been dropped and recreated
-- Database is now in a clean state
-- ============================================================================
