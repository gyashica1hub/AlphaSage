PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT,
    password_hash TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolios (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolio_positions (
    id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    quantity REAL NOT NULL CHECK (quantity >= 0),
    average_buy_price REAL NOT NULL CHECK (average_buy_price >= 0),
    sector TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (portfolio_id, symbol)
);

CREATE TABLE IF NOT EXISTS watchlists (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlist_items (
    id TEXT PRIMARY KEY,
    watchlist_id TEXT NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (watchlist_id, symbol)
);

CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio_id ON portfolio_positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON watchlists(user_id);
