-- Stock Screener Database Schema

CREATE TABLE IF NOT EXISTS companies (
    ticker              TEXT PRIMARY KEY,
    exchange            TEXT,
    market              TEXT NOT NULL,
    name                TEXT,
    sector              TEXT,
    industry            TEXT,
    cik                 TEXT,
    isin                TEXT,
    index_membership    TEXT,
    has_fundamentals    INTEGER NOT NULL DEFAULT 0,
    is_active           INTEGER NOT NULL DEFAULT 1,
    last_seen_at        TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_companies_market ON companies(market);
CREATE INDEX IF NOT EXISTS idx_companies_has_fundamentals ON companies(has_fundamentals);

CREATE TABLE IF NOT EXISTS prices (
    ticker      TEXT NOT NULL,
    date        TEXT NOT NULL,
    open REAL, high REAL, low REAL, close REAL, adj_close REAL,
    volume      INTEGER,
    PRIMARY KEY (ticker, date),
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);
CREATE INDEX IF NOT EXISTS idx_prices_ticker_date ON prices(ticker, date);

CREATE TABLE IF NOT EXISTS technicals_latest (
    ticker TEXT PRIMARY KEY,
    as_of_date TEXT NOT NULL,
    price REAL,
    sma20 REAL, sma50 REAL, sma150 REAL, sma200 REAL, sma220 REAL, ema220 REAL,
    ema12 REAL, ema26 REAL,
    rsi14 REAL,
    macd REAL, macd_signal REAL, macd_hist REAL,
    bb_upper REAL, bb_lower REAL, bb_mid REAL, bb_percent_b REAL,
    pct_change_1d REAL, pct_change_1m REAL, pct_change_3m REAL, pct_change_1y REAL,
    pct_from_52w_high REAL, pct_from_52w_low REAL,
    "52w_low" REAL, "52w_low_25pct" REAL,
    volume INTEGER, avg_volume_20d INTEGER, volume_spike_ratio REAL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

CREATE TABLE IF NOT EXISTS fundamentals (
    ticker           TEXT NOT NULL,
    fiscal_period    TEXT NOT NULL,
    period_end_date  TEXT,
    line_item_key    TEXT NOT NULL,
    line_item_label  TEXT,
    value            REAL,
    unit             TEXT,
    source           TEXT NOT NULL,
    is_custom        INTEGER NOT NULL DEFAULT 0,
    fetched_at       TEXT NOT NULL,
    PRIMARY KEY (ticker, fiscal_period, line_item_key),
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);
CREATE INDEX IF NOT EXISTS idx_fundamentals_ticker ON fundamentals(ticker);
CREATE INDEX IF NOT EXISTS idx_fundamentals_line_item ON fundamentals(line_item_key);

CREATE TABLE IF NOT EXISTS fundamentals_latest (
    ticker TEXT PRIMARY KEY,
    fiscal_period TEXT,
    pe_ratio REAL, forward_pe REAL, pb_ratio REAL, debt_to_equity REAL,
    roe REAL, profit_margin REAL, revenue_growth REAL, earnings_growth REAL,
    dividend_yield REAL, market_cap REAL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

CREATE TABLE IF NOT EXISTS custom_line_items (
    line_item_key TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Fundamental',
    unit TEXT,
    description TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    definition_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS data_refresh_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_type TEXT NOT NULL,
    market TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    tickers_attempted INTEGER,
    tickers_succeeded INTEGER,
    tickers_failed INTEGER,
    failed_tickers_json TEXT,
    error_summary TEXT,
    notes TEXT
);
