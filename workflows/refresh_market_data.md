# Refresh Market Data

## Objective
Keep the stock screener cache fresh with current prices, technicals, and fundamentals.

## Required Inputs
- `market`: "US", "IN", or "ALL"
- `scope`: "full" (all stocks) or "test" (S&P 100 + Nifty 50 for verification)
- `period`: Historical lookback (e.g., "1y", "2y", "5y")

## Tools Used (in dependency order)
1. **`tools/build_universe.py`** — Fetch current ticker universe (runs once, then on-demand)
2. **`tools/refresh_prices.py`** — Fetch OHLCV from yfinance, compute technicals
3. **`tools/refresh_us_fundamentals.py`** — Fetch US fundamentals from SEC EDGAR XBRL
4. **`tools/refresh_india_fundamentals.py`** — (v2+) India fundamentals from Screener.in or paid API

## Expected Outputs
- Updated `companies` table (tickers, exchanges, CIK, index membership)
- Updated `prices` table (daily OHLCV for all tickers)
- Updated `technicals_latest` table (SMA, RSI, MACD, Bollinger Bands, etc.)
- Updated `fundamentals` table (10-yr financial line items for US; Nifty500/BSE500 for India)
- Log entries in `data_refresh_log` tracking success/failure per tool

## Edge Cases & Handling

### yfinance Rate Limiting
- **Issue**: yfinance gets 429s after ~5,000 tickers on a single connection
- **Handling**: Implemented via `tools/refresh_prices.py` with batch throttling (75 tickers/batch, 2s sleep between)
- **If it fails**: Check network, retry with `--tickers <list>` to focus on a subset
- **Long-term**: Consider switching to Polygon.io or other commercial price APIs if yfinance becomes unreliable

### SEC EDGAR User-Agent
- **Issue**: SEC blocks requests without a descriptive User-Agent including contact info
- **Handling**: Stored in `.env` as `SEC_EDGAR_USER_AGENT`
- **If it fails**: Check `.env` has valid email address

### Screener.in Scraping (India Fundamentals, v2+)
- **Issue**: Web scraping is fragile — layout changes, IP blocking, rate-limiting
- **Current Status**: Not implemented in v1 (placeholder in `stockscreener/screener_in.py`)
- **v1 Workaround**: India stocks get technicals only; fundamentals available for Nifty500/BSE500 tier only
- **Future options**:
  - Tickertape's JSON endpoints (faster, but undocumented)
  - Zerodha Kite API (free, if you have a brokerage account)
  - Tijori Finance API
  - Pay for a financial data subscription

### Missing Data
- **Tickers with no price data**: Logged to `data_refresh_log.failed_tickers_json`, skip silently
- **US stocks with no CIK match**: Set `has_fundamentals=0`, skip fundamental refresh for them
- **India stocks outside Nifty500/BSE500**: Set `has_fundamentals=0`, only get technicals

## Typical Run
```bash
# First time: build universe (one-off)
python tools/build_universe.py --market ALL

# Recurring: refresh prices + technicals (daily/weekly)
python tools/refresh_prices.py --market ALL --period 2y

# US fundamentals (quarterly/annually — SEC filings are not real-time)
python tools/refresh_us_fundamentals.py

# Check status
python tools/verify_db.py
```

## Verification
- `tools/verify_db.py` checks row counts, staleness, and spot-checks one ticker against live sources
- Spot-check technicals manually: compute RSI/SMA on a spreadsheet for one ticker, compare with DB
- For US fundamentals: spot-check one ticker's revenue/EPS against SEC EDGAR's own viewer (`https://www.sec.gov/cgi-bin/browse-edgar`)
- For prices: compare against Yahoo Finance or trading platform charts

## Performance Notes
- **First-time universe build**: ~1 min (fetching ~5000 tickers from NSE/SEC)
- **First-time price backfill**: ~30-60 min (10,000 tickers × 2 years of daily bars, throttled)
- **Incremental price refresh**: ~5-10 min (new data only, throttled)
- **US fundamentals**: ~15-30 min for all US tickers (depends on SEC's responsiveness)
- **Technicals computation**: Included in price refresh, no additional time

## Scheduling (Recommended for v2+)
- **Universe build**: Once per month (when new IPOs/delistings expected)
- **Price + technicals**: Daily, before market hours (for next-day screening)
- **US fundamentals**: Quarterly (after earnings season, when SEC filings are published)
- **India fundamentals**: Quarterly (when NSE publishes consolidated reports)
