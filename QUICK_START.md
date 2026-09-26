# Quick Start - 5 Minutes to Dashboard

## Copy-Paste Commands

### Step 1: Activate Virtual Environment

```bash
.venv\Scripts\activate
```

### Step 2: Install Dependencies (if not done)

```bash
pip install -r requirements.txt
```

### Step 3: Start Dashboard

```bash
streamlit run dashboard/app.py
```

### Step 4: Open Browser

👉 Go to: **http://localhost:8501**

---

## You're Done! 🎉

The dashboard is now running. You'll see:

```
📊 Dashboard
├── 📈 Overview (KPIs, data status)
├── 🛠️ Strategy Builder (create strategies)
├── 🔍 Run Screener (test strategies)
├── 📋 Fundamentals (view company data)
└── 🔄 Data Refresh (fetch market data)
```

---

## 5-Minute Workflow

### 1. Explore Metrics (30 seconds)

Go to **Strategy Builder** page → scroll down to see all 60+ metrics:
- sma20, sma50, **sma150**, **sma220**, **ema220** ← NEW
- price, **52w_low**, **52w_low_25pct** ← NEW
- rsi14, pe_ratio, etc.

### 2. Create Your First Strategy (2 minutes)

Go to **Strategy Builder** page → paste this JSON:

```json
{
  "name": "220 EMA Breakout",
  "root": {
    "logic": "AND",
    "items": [
      {"metric": "sma150", "operator": ">", "compare_type": "metric", "compare_metric": "ema220"},
      {"metric": "price", "operator": ">", "compare_type": "metric", "compare_metric": "sma50"},
      {"metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma150"},
      {"metric": "price", "operator": ">", "compare_type": "metric", "compare_metric": "52w_low_25pct"},
      {"condition_type": "dipped_below", "compare_level": "ema220", "days": 90}
    ]
  }
}
```

Click **Save Strategy** ✅

### 3. View Saved Strategies (30 seconds)

Scroll down to **Saved Strategies** section → see your strategy in the list

### 4. Test It (1.5 minutes)

⚠️ **Before testing:** You need stock data in the database

**Option A:** If you have data from before:
1. Go to **Run Screener**
2. Select your strategy
3. Click "Run Strategy"

**Option B:** If no data yet:
1. Go to **Data Refresh**
2. Click "Refresh US Companies Universe"
3. Click "Refresh Price Data" (takes 30-60 min)
4. Then go to Run Screener and test

---

## Most Useful Pages

| Page | What It Does | Key Action |
|------|-------------|-----------|
| **Strategy Builder** | Define AND/OR conditions | Click "Save Strategy" |
| **Run Screener** | Test strategy on stocks | Select strategy → "Run Strategy" |
| **Data Refresh** | Fetch/update market data | Click "Refresh..." buttons |
| **Dashboard** | See overview & data status | Just view, read-only |
| **Fundamentals** | Lookup company P/E, profit margin, etc. | Search for ticker |

---

## Your New Metrics (Ready to Use)

```
Moving Averages:
  ✨ sma150      150-day Simple Moving Average (NEW)
  ✨ sma220      220-day Simple Moving Average (NEW)
  ✨ ema220      220-day Exponential Average (NEW)

Support Levels:
  ✨ 52w_low           52-week Low (NEW)
  ✨ 52w_low_25pct    52-week Low × 1.25 (NEW)

Special Condition:
  ✨ dipped_below     Check if price touched level in past N days (NEW)
```

---

## Example Strategies to Try

### 1. Golden Cross (Simple)

```json
{
  "name": "Golden Cross",
  "root": {
    "logic": "AND",
    "items": [
      {"metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma200"},
      {"metric": "price", "operator": ">", "compare_type": "metric", "compare_metric": "sma50"}
    ]
  }
}
```

### 2. Oversold Value (Fundamental)

```json
{
  "name": "Oversold Value",
  "root": {
    "logic": "AND",
    "items": [
      {"metric": "rsi14", "operator": "<", "compare_type": "value", "value": 35.0},
      {"metric": "pe_ratio", "operator": "<", "compare_type": "value", "value": 20.0}
    ]
  }
}
```

### 3. Mean Reversion (Advanced)

```json
{
  "name": "Mean Reversion",
  "root": {
    "logic": "AND",
    "items": [
      {"metric": "rsi14", "operator": "<", "compare_type": "value", "value": 30.0},
      {"metric": "pct_change_1m", "operator": "<", "compare_type": "value", "value": -10.0},
      {"metric": "bb_percent_b", "operator": "<", "compare_type": "value", "value": 0.2}
    ]
  }
}
```

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Stop dashboard | `Ctrl + C` |
| Reload app | `R` (in browser) |
| Clear cache | `Ctrl + K` then `C` |

---

## Common Issues & Fixes

**Dashboard won't start?**
```bash
# Kill any existing process
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Then restart
streamlit run dashboard/app.py
```

**No data to screen?**
1. Go to **Data Refresh** page
2. Click "Refresh US Companies"
3. Click "Refresh Price Data"
4. Wait 30-60 minutes

**Strategy won't save?**
1. Make sure JSON is valid (use [jsonlint.com](https://jsonlint.com) to validate)
2. Make sure all metric names exist
3. Try simple 2-condition strategy first

**Port 8501 already in use?**
```bash
streamlit run dashboard/app.py --server.port 8502
# Then go to http://localhost:8502
```

---

## Next Level

Once you're comfortable:

- **See all metrics:** `python tools/example_strategies.py --list-metrics`
- **Read full guide:** Open [STRATEGY_BUILDER_GUIDE.md](STRATEGY_BUILDER_GUIDE.md)
- **One-page reference:** Open [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **What changed:** Open [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)

---

## That's It!

**You now have:**
✅ Fully flexible strategy builder (no fixed conditions)  
✅ 6 new metrics for technical analysis  
✅ Historical lookback conditions (dipped_below)  
✅ AND/OR logic for complex strategies  
✅ Interactive dashboard to build, test, and manage strategies  

**Start with:** `streamlit run dashboard/app.py` 🚀
