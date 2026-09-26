# Professional Stock Screener — Getting Started

## 🎯 What You've Built

A **local web-based stock screener dashboard** for US and Indian markets. Define strategies (no-code AND/OR rule builder), run them against cached data, and analyze fundamentals up to 10 years back — all running on your computer.

**Architecture**: WAT framework (Workflows/Agents/Tools) with SQLite cache, Streamlit UI, free data sources (SEC EDGAR for US fundamentals, yfinance for prices, Screener.in-ready for India).

---

## 🚀 Quick Start

### 1. Set Up Environment

```bash
cd "C:\Users\goura\OneDrive\Desktop\Creating AI Agents\MyProjectUnderstanding"

# If first time: install dependencies
pip install -r requirements.txt

# Verify setup
python -c "from stockscreener.db import init_db; init_db(); print('✓ Database initialized')"
```

### 2. Populate Initial Data (Test Mode)

```bash
# Build ticker universe (S&P 100 US + Nifty 50 India — for testing)
python tools/build_universe.py --market ALL

# Fetch prices + compute technicals (last 2 years)
python tools/refresh_prices.py --market ALL --period 2y

# Fetch US fundamentals from SEC EDGAR
python tools/refresh_us_fundamentals.py --tickers AAPL MSFT JPM BRK-B V
```

### 3. Launch Dashboard

```bash
streamlit run dashboard/app.py
```

Opens `http://localhost:8501` — you should see:
- **Dashboard tab**: KPI tiles, last-refresh timestamps
- **Strategy Builder**: Edit the 2 pre-loaded example strategies or create new ones
- **Run Screener**: Execute a strategy against US/India stocks
- **Fundamentals**: View 10-year financial data for any stock
- **Data Refresh**: Status of pipelines (currently shows instructions; v2 will make it interactive)

---

## 📊 Example Workflow

### Scenario: Find oversold value stocks

1. **Go to Strategy Builder**
   - Load "Oversold Value Pick" (pre-loaded example)
   - Review conditions: RSI < 35 AND P/E < 25
   - Or create new: add conditions as you like
   - Click "Save Strategy"

2. **Go to Run Screener**
   - Pick your strategy
   - Choose market (US, India, or Both)
   - Choose scope (Full Universe, Index Only, or Custom list)
   - Click "Run Screener"
   - Download results as CSV

3. **Go to Fundamentals**
   - Pick a stock from results
   - Expand each line item to see 10-year trend
   - Check if P/E is truly low, margin trends, debt levels
   - Make investment decision

---

## 📈 Scaling to Full Universe

Currently set up for **test mode** (S&P 100 + Nifty 50 = 89 stocks). To scale to full universe:

```bash
# Full US universe (~5000+ tickers)
python tools/build_universe.py --market US --full

# Full India universe (~5000+ tickers, technicals only; fundamentals tier: Nifty500/BSE500)
python tools/build_universe.py --market IN --full

# Then refresh prices for full universe
python tools/refresh_prices.py --market ALL --period 2y --full

# Refresh US fundamentals (will take 15-30 min depending on SEC EDGAR speed)
python tools/refresh_us_fundamentals.py
```

### ⚠️ Performance Notes
- **First-time backfill** (all tickers × 2 years of prices): ~30–60 minutes
- **Incremental price refresh** (new data only): ~5–10 minutes
- **US fundamentals** (all tickers): ~15–30 minutes
- **India fundamentals** (v1): Not implemented. v2 will add Screener.in or paid API option.

---

## 🔧 Architecture Overview

```
MyProjectUnderstanding/
├── stockscreener/              # Shared library (DB, metrics, engine)
│   ├── db.py                  # Database connection & helpers
│   ├── schema.sql             # SQLite schema
│   ├── metrics.py             # Built-in + custom metrics registry
│   ├── strategy_engine.py     # AND/OR strategy evaluation & CRUD
│   ├── technicals.py          # SMA, RSI, MACD, Bollinger Bands, etc.
│   ├── us_tickers.py          # US universe building
│   ├── india_tickers.py       # India universe building
│   ├── sec_edgar.py           # US fundamentals via SEC EDGAR XBRL
│   ├── yfinance_client.py     # Throttled yfinance wrapper
│   └── screener_in.py         # India fundamentals stub (v2+)
│
├── tools/                     # One-shot execution scripts
│   ├── build_universe.py      # Populate companies table
│   ├── refresh_prices.py      # Fetch OHLCV, compute technicals
│   ├── refresh_us_fundamentals.py  # SEC EDGAR pipeline
│   ├── refresh_india_fundamentals.py  # Screener.in stub (v2+)
│   └── migrate_legacy_strategies.py   # Prototype → v1 migration
│
├── dashboard/                 # Streamlit multi-page app
│   ├── app.py                # Landing page, KPI tiles
│   └── pages/
│       ├── 1_Strategy_Builder.py
│       ├── 2_Run_Screener.py
│       ├── 3_Fundamentals.py
│       └── 4_Data_Refresh.py
│
├── workflows/                 # WAT SOPs (markdown documentation)
│   ├── refresh_market_data.md
│   ├── define_strategy.md
│   ├── run_screener.md
│   └── review_fundamentals.md
│
├── data/
│   └── stock_screener.db      # SQLite database (created at runtime)
│
├── requirements.txt           # Dependencies
├── .env                       # SEC_EDGAR_USER_AGENT
└── CLAUDE.md                  # WAT framework instructions

Database schema:
  companies          — tickers, exchanges, CIK, index membership, has_fundamentals flag
  prices             — daily OHLCV
  technicals_latest  — precomputed SMA/RSI/MACD/Bollinger/volume metrics
  fundamentals       — 10-yr financial line items (tidy/long format)
  fundamentals_latest  — current ratios (PE, PB, ROE, etc.)
  custom_line_items  — registry of user-added tracking items
  strategies         — saved AND/OR strategy definitions (JSON)
  data_refresh_log   — audit log of pipeline runs
```

---

## 📋 Supported Metrics

### Technical (31 built-in)
- **Price**: Current, SMA20/50/200, RSI14, MACD, Bollinger Bands
- **Momentum**: % change 1d/1m/3m/1y, % from 52-week high/low
- **Volume**: Current, 20-day average, spike ratio

### Fundamental (10 built-in, extensible)
- **Valuation**: P/E, Forward P/E, P/B, Debt/Equity
- **Profitability**: ROE, Profit Margin
- **Growth**: Revenue Growth, Earnings Growth
- **Yield**: Dividend Yield, Market Cap

### Custom (User-added in v2)
- Add any line item from company filings to track alongside standards

---

## 🌍 Data Coverage

### United States ✅ (Full v1 Support)
- **Tickers**: ~5,000+ (NYSE + NASDAQ)
- **Prices**: 2 years+ daily OHLCV via yfinance
- **Fundamentals**: 10 years via SEC EDGAR XBRL (all filers with CIK)
- **Status**: Reliable and free

### India 🇮🇳 (Tiered v1 Support)
- **Tickers**: ~5,000+ (NSE + BSE)
- **Prices**: 2 years+ daily OHLCV via yfinance (coverage varies by liquidity)
- **Fundamentals**:
  - ✅ **Nifty 500 + BSE 500** (~700–900 stocks): Ready for v2 (Screener.in or paid API)
  - ❌ **Full universe (5,000+)**: No free comprehensive source; technicals only in v1
- **Note**: India fundamentals stubbed in v1; awaiting Screener.in scraping or paid API integration

---

## 🛠️ Advanced: Running Tools from CLI

```bash
# Build/refresh universe
python tools/build_universe.py --market ALL [--full]

# Refresh prices + technicals
python tools/refresh_prices.py --market US [--period 5y] [--tickers AAPL MSFT ...]

# Refresh US fundamentals
python tools/refresh_us_fundamentals.py [--tickers AAPL MSFT ...]

# Verify data quality
python tools/verify_db.py

# Migrate legacy strategies (one-time)
python tools/migrate_legacy_strategies.py
```

Each tool logs to `data_refresh_log` table for audit trail.

---

## 🐛 Troubleshooting

### Dashboard won't start
```bash
# Check dependencies
pip install -r requirements.txt --upgrade

# Check database
python -c "from stockscreener.db import init_db; init_db(); print('✓ OK')"
```

### No strategies showing
```bash
# Load the 2 examples
python tools/migrate_legacy_strategies.py
```

### Prices/fundamentals empty
```bash
# Refresh data (this will take a while first time)
python tools/refresh_prices.py --market US --period 2y
python tools/refresh_us_fundamentals.py
```

### SEC EDGAR rate limiting (ERRORs in logs)
- SEC limits to 10 req/sec. Implemented throttling in `refresh_us_fundamentals.py`.
- If you still hit 429s: either SEC's servers are slow, or your IP is temporarily blocked.
- Workaround: wait 30 mins or try again on a different network.

### yfinance errors (missing tickers)
- yfinance is an unofficial scraper → Yahoo Finance can break it without notice.
- Check if ticker is correct and tradeable.
- If stock is newly IPO'd or delisted, it may not be available yet.

---

## 📚 Documentation

- **`workflows/refresh_market_data.md`** — How to refresh cache (tools, edge cases, scheduling)
- **`workflows/define_strategy.md`** — Strategy schema, examples, validation
- **`workflows/run_screener.md`** — Execution workflow, tips, verification
- **`workflows/review_fundamentals.md`** — Analysis workflow, line items, deep dives
- **`CLAUDE.md`** — WAT framework philosophy (Workflows/Agents/Tools)

---

## 🚀 Next Steps (v2 Roadmap)

- ✅ **v1 Complete**: US fundamentals (free via SEC), strategy builder, fundamentals tab
- 🎯 **v2 Planned**:
  - India fundamentals (Screener.in integration or paid API)
  - Backtesting: see how strategies would have performed historically
  - Interactive charts (Plotly with zoom/pan)
  - Custom metrics (user-defined formulas)
  - Scheduled runs + email alerts
  - Peer comparison / relative valuation
  - Multi-factor ranking (don't just screen, rank results)

---

## 💡 Tips for Best Results

1. **Start with fundamentals**: Know your data. Pick a stock you're familiar with, check its fundamentals in the app, compare with the company's website or SEC filings.

2. **Test strategies on small universes first**: Create a strategy, run it on a custom list of 10-20 tickers you know well. Do the results make sense?

3. **Iterate on rules**: Save multiple strategy variants (e.g., "Value Pick v1", "Value Pick v2" with tighter P/E). See which works better historically (backtesting in v2).

4. **Combine technical + fundamental**: Best strategies use both. Example: "Golden Cross Momentum (technical) + Value Check (P/E < 20) (fundamental)" = momentum + valuation.

5. **Keep data fresh**: Run `python tools/refresh_prices.py --market ALL` daily or weekly to stay current.

---

## 📞 Support

For questions, bugs, or feature requests:
- Check `CLAUDE.md` for WAT framework architecture notes
- Check workflow docs (`workflows/`) for operational guidance
- Review database schema in `stockscreener/schema.sql`

Enjoy your stock screening! 📈

---

**Version**: 1.0 (Beta)  
**Built**: 2026-09-26  
**Framework**: WAT (Workflows/Agents/Tools)
