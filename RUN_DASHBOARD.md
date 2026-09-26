# How to Run the Updated Dashboard

The dashboard is built with **Streamlit**, a Python framework for building interactive data apps. Here's how to get it running with your new flexible strategy builder.

---

## Prerequisites

✅ Python 3.8+ installed  
✅ Project files from this directory  
✅ Virtual environment (recommended)

---

## Step 1: Set Up Environment

### 1a. Create Virtual Environment (if not already done)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 1b. Install Dependencies

```bash
pip install -r requirements.txt
```

**What gets installed:**
- streamlit (dashboard framework)
- pandas, numpy (data processing)
- yfinance (stock price data)
- plotly (charts)
- google-api-python-client (Google Sheets integration)
- And more...

---

## Step 2: Configure Environment

### 2a. Create .env file

Copy the template and fill in your settings:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# SEC EDGAR configuration (required for US fundamentals)
SEC_EDGAR_USER_AGENT=StockScreenerDashboard (your.email@example.com)
```

**Note:** The email is used to identify your requests to SEC. Use any valid format.

### 2b. Initialize Database

The database will be created automatically on first run, but you can initialize it manually:

```bash
python -c "from stockscreener.db import init_db; init_db()"
```

This creates `data/stock_screener.db` with all tables for companies, prices, technicals, strategies, etc.

---

## Step 3: Run the Dashboard

### Start Streamlit Server

```bash
streamlit run dashboard/app.py
```

**Output should look like:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### Open in Browser

👉 **Go to:** `http://localhost:8501`

You should see the Stock Screener dashboard with 5 pages in the sidebar:
- 📊 Dashboard (overview & data status)
- 🛠️ Strategy Builder (define your strategies)
- 🔍 Run Screener (test strategies)
- 📋 Fundamentals (analyze company data)
- 🔄 Data Refresh (fetch market data)

---

## Step 4: Load Sample Data (Optional)

Before running strategies, you'll need some stock data. Choose one:

### Option A: Use Existing Data (if you have it)

If you already have `data/stock_screener.db` with companies and prices, you're ready to go.

### Option B: Refresh Data from Scratch

In the dashboard, go to **🔄 Data Refresh** page:

1. Click "Refresh US Companies Universe"
2. Click "Refresh Price Data" 
3. Click "Compute Technicals"

This will:
- Download all US companies from Yahoo Finance
- Fetch 2+ years of price history
- Calculate all technical indicators (including your new ones: sma150, sma220, ema220)
- Store in the database

⚠️ **Warning:** This takes 30-60 minutes depending on internet speed.

### Option C: Quick Test with Few Stocks

Use the example script instead:

```bash
python tools/example_strategies.py --list-metrics
python tools/example_strategies.py --save
```

This saves 3 example strategies (including 220 EMA Breakout) without needing to fetch data.

---

## Step 5: Use the Strategy Builder

### 5a. View Available Metrics

In the **Strategy Builder** page, scroll down to see all 60+ available metrics organized by category:
- Moving Averages (including new: sma150, sma220, ema220)
- Price Support (new: 52w_low, 52w_low_25pct)
- Momentum, Volume, Fundamentals, etc.

### 5b. Define Your Strategy

Example: Create the **220 EMA Breakout** strategy

1. Click **"Strategy Builder"** in sidebar
2. Enter name: `220 EMA Breakout`
3. Add conditions (as JSON):

```json
{
  "root": {
    "logic": "AND",
    "items": [
      {
        "metric": "sma150",
        "operator": ">",
        "compare_type": "metric",
        "compare_metric": "ema220"
      },
      {
        "metric": "price",
        "operator": ">",
        "compare_type": "metric",
        "compare_metric": "sma50"
      },
      {
        "metric": "sma50",
        "operator": ">",
        "compare_type": "metric",
        "compare_metric": "sma150"
      },
      {
        "metric": "price",
        "operator": ">",
        "compare_type": "metric",
        "compare_metric": "52w_low_25pct"
      },
      {
        "condition_type": "dipped_below",
        "compare_level": "ema220",
        "days": 90
      }
    ]
  }
}
```

4. Click "Save Strategy"
5. Strategy is now stored in the database

### 5c. Run Your Strategy

1. Go to **"Run Screener"** page
2. Select your strategy from dropdown
3. Choose tickers to screen (or "All")
4. Click "Run Strategy"
5. See matching stocks in results table

---

## Step 6: Common Tasks

### View All Saved Strategies

**Dashboard → Strategy Builder:**
- Scroll to "Saved Strategies" section
- See all strategies with their conditions

### Export Results

**Dashboard → Run Screener:**
- Run a strategy
- Click "Download as CSV" button
- Results saved to your computer

### Refresh Data

**Dashboard → Data Refresh:**
- Refresh prices: `Refresh Price Data`
- Refresh fundamentals: `Refresh US Fundamentals`
- This updates technicals including your new metrics

### View Company Fundamentals

**Dashboard → Fundamentals:**
- Search for a stock (e.g., "AAPL")
- See P/E ratio, profit margin, ROE, etc.
- Used for building fundamental conditions

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'stockscreener'"

**Solution:** Make sure you're running from the project root directory, or activate the virtual environment:

```bash
# Ensure you're in the right directory
cd C:\Users\goura\OneDrive\Desktop\Creating\ AI\ Agents\MyProjectUnderstanding

# Activate venv
.venv\Scripts\activate

# Run dashboard
streamlit run dashboard/app.py
```

### Error: "StreamlitAPIException: Cannot write to AppData"

**Solution:** Run PowerShell as Administrator, or set Streamlit config:

```bash
streamlit run dashboard/app.py --logger.level=debug
```

### Error: "database is locked"

**Solution:** Close any other processes accessing the database and restart:

```bash
# Kill streamlit
Ctrl + C

# Wait 5 seconds, then restart
streamlit run dashboard/app.py
```

### No strategies appearing in Run Screener

**Solution:** Save a strategy first:
1. Go to Strategy Builder
2. Enter strategy JSON
3. Click "Save Strategy"
4. Go to Run Screener and refresh page

### No data/stocks to screen

**Solution:** Fetch data first:
1. Go to Data Refresh
2. Click "Refresh US Companies"
3. Click "Refresh Price Data"
4. Wait for completion
5. Then run strategies

---

## Development Mode

For faster iteration while developing:

```bash
# Run with auto-reload on file changes
streamlit run dashboard/app.py --logger.level=debug

# Or with Python debugger
python -m pdb dashboard/app.py
```

---

## Performance Tips

1. **Narrow ticker universe** when testing
   - Test on 10 stocks first, then expand

2. **Cache data locally**
   - First run fetches data, subsequent runs use cached DB

3. **Use simple strategies first**
   - 2-3 conditions faster than 5+ conditions

4. **Refresh data weekly**
   - Run Data Refresh → "Refresh Price Data" weekly
   - Keeps strategies current

---

## File Structure Reference

```
project_root/
├── dashboard/
│   ├── app.py                    ← Main Streamlit app (run this)
│   └── pages/
│       ├── 1_Strategy_Builder.py ← Define strategies
│       ├── 2_Run_Screener.py     ← Test strategies
│       ├── 3_Fundamentals.py     ← View company data
│       └── 4_Data_Refresh.py     ← Fetch/refresh data
├── stockscreener/
│   ├── strategy_engine.py        ← Condition evaluation (UPDATED)
│   ├── metrics.py                ← Available metrics (UPDATED)
│   ├── technicals.py             ← Technical calculations (UPDATED)
│   ├── db.py                     ← Database operations
│   └── schema.sql                ← Database schema (UPDATED)
├── tools/
│   └── example_strategies.py     ← Programmatic examples (NEW)
├── data/
│   └── stock_screener.db         ← SQLite database (auto-created)
├── QUICK_REFERENCE.md            ← One-page cheat sheet (NEW)
├── STRATEGY_BUILDER_GUIDE.md     ← Complete guide (NEW)
└── requirements.txt              ← Python dependencies
```

---

## Next Steps

1. ✅ **Run the dashboard** → `streamlit run dashboard/app.py`
2. ✅ **Load some data** → Use Data Refresh page
3. ✅ **Create your first strategy** → Strategy Builder page
4. ✅ **Test it** → Run Screener page
5. ✅ **Iterate** → Adjust conditions, test again

---

## Questions?

- **Strategy syntax** → See [STRATEGY_BUILDER_GUIDE.md](STRATEGY_BUILDER_GUIDE.md)
- **Quick reference** → See [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Available metrics** → Strategy Builder page → scroll down
- **Examples** → Run `python tools/example_strategies.py --syntax`

**Happy screening! 🚀**
