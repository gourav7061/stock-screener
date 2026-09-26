# 🚀 START HERE - Complete Guide Index

**Your flexible strategy builder is ready!** This index shows you exactly where to go for what you need.

---

## 📋 Quick Navigation

### I Just Want to Run It
👉 **[QUICK_START.md](QUICK_START.md)** (5 minutes)
- Copy-paste 3 commands
- Dashboard is running
- Try your first strategy

### I Want Step-by-Step Instructions
👉 **[RUN_DASHBOARD.md](RUN_DASHBOARD.md)** (20 minutes)
- Detailed setup steps
- Environment configuration
- Data loading options
- Common troubleshooting

### I Want to Build Custom Strategies
👉 **[STRATEGY_BUILDER_GUIDE.md](STRATEGY_BUILDER_GUIDE.md)** (30 minutes)
- Complete syntax guide
- Pattern examples
- Advanced nesting
- 60+ available metrics explained

### I Want a One-Page Reference
👉 **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** (2 minutes)
- Metrics cheat sheet
- Operators & patterns
- Common examples
- Copy-paste templates

### I Want to Know What Changed
👉 **[CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)** (15 minutes)
- Technical changes
- New metrics (sma150, sma220, ema220, 52w_low, etc.)
- New condition types (dipped_below)
- Breaking changes (none!)

---

## 🎯 Your Use Case

### Use Case 1: "Just Show Me the Dashboard"
1. **[QUICK_START.md](QUICK_START.md)** - Run it in 5 minutes
2. Explore the 5 pages in the sidebar
3. Done!

### Use Case 2: "I Want to Use the 220 EMA Breakout Strategy"
1. **[QUICK_START.md](QUICK_START.md)** - Get dashboard running
2. Go to **Strategy Builder** page
3. Paste the JSON from [QUICK_START.md](QUICK_START.md) (section "Create Your First Strategy")
4. Click "Save Strategy"
5. Go to **Run Screener** page
6. Select your strategy and test
7. ✅ Done!

### Use Case 3: "I Want to Build My Own Custom Strategy"
1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Learn syntax (2 min)
2. **[STRATEGY_BUILDER_GUIDE.md](STRATEGY_BUILDER_GUIDE.md)** - See patterns (10 min)
3. Dashboard **Strategy Builder** page - write your JSON
4. Test it on **Run Screener** page
5. Iterate until satisfied

### Use Case 4: "I Want to Understand All the Changes"
1. **[CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)** - See what's new
2. **[STRATEGY_BUILDER_GUIDE.md](STRATEGY_BUILDER_GUIDE.md)** - See how to use it
3. Run `python tools/example_strategies.py --list-metrics` - see all metrics

### Use Case 5: "I'm a Programmer, Show Me the Code"
1. Check the updated files:
   - `stockscreener/metrics.py` - New metrics definitions
   - `stockscreener/technicals.py` - New computation functions
   - `stockscreener/strategy_engine.py` - New "dipped_below" condition
   - `stockscreener/schema.sql` - New database columns
2. See examples in `tools/example_strategies.py`
3. Read [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) for technical details

---

## 📊 What's New (TL;DR)

### New Metrics
- `sma150` - 150-day Simple Moving Average
- `sma220` - 220-day Simple Moving Average
- `ema220` - 220-day Exponential Moving Average
- `52w_low` - 52-week low price
- `52w_low_25pct` - 52-week low × 1.25

### New Special Condition
- `dipped_below` - Check if price touched a level in past N days

### Your 5 Conditions from Screenshot
1. ✅ 150SMA > 220EMA
2. ✅ Price > 50SMA
3. ✅ 50SMA > 150SMA
4. ✅ Price > 1.25 × 52-week low
5. ✅ Dipped below 220EMA in past 90 days
6. ✅ Signals on closing price (automatic)

**All supported!** 🎉

---

## 🏃 Fastest Path: 3 Steps

```bash
# Step 1: Activate environment
.venv\Scripts\activate

# Step 2: Run dashboard
streamlit run dashboard/app.py

# Step 3: Open browser
# → http://localhost:8501
```

Done! You're in the dashboard. Now:
1. Go to **Strategy Builder** page
2. Paste any strategy JSON
3. Click "Save Strategy"
4. Go to **Run Screener** page
5. Test it

---

## 📚 Document Directory

| Document | Purpose | Time | Audience |
|----------|---------|------|----------|
| **[QUICK_START.md](QUICK_START.md)** | Get running in 5 min | 5 min | Everyone |
| **[RUN_DASHBOARD.md](RUN_DASHBOARD.md)** | Detailed setup guide | 20 min | Users setting up |
| **[STRATEGY_BUILDER_GUIDE.md](STRATEGY_BUILDER_GUIDE.md)** | Complete strategy docs | 30 min | Strategy builders |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | One-page cheat sheet | 2 min | In-dashboard reference |
| **[CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)** | What changed & why | 15 min | Technical/curious |

---

## 💡 Pro Tips

### Tip 1: Validate JSON Before Saving
Paste strategy JSON at [jsonlint.com](https://jsonlint.com) to catch syntax errors early.

### Tip 2: Start Simple, Then Expand
Build 2-condition strategy first, test it, then add more conditions.

### Tip 3: Use the Examples
Run this to see pre-built strategies:
```bash
python tools/example_strategies.py --syntax
```

### Tip 4: Check Available Metrics
In dashboard **Strategy Builder** page, scroll to see all 60+ metrics, OR run:
```bash
python tools/example_strategies.py --list-metrics
```

### Tip 5: Narrow Universe When Testing
Test strategy on 10 stocks first (e.g., AAPL, MSFT, GOOGL) before running on thousands.

---

## 🆘 Help & Support

### Dashboard won't start?
→ See [RUN_DASHBOARD.md](RUN_DASHBOARD.md) → Troubleshooting section

### Strategy syntax error?
→ See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) → Common Patterns section
→ OR See [STRATEGY_BUILDER_GUIDE.md](STRATEGY_BUILDER_GUIDE.md) → Examples section

### Don't know what metrics to use?
→ Run `python tools/example_strategies.py --list-metrics`
→ OR See [STRATEGY_BUILDER_GUIDE.md](STRATEGY_BUILDER_GUIDE.md) → Available Metrics section

### Want to understand the changes?
→ See [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)

### Want to use it programmatically (not dashboard)?
→ See `tools/example_strategies.py` for Python examples

---

## 🎓 Learning Path

**Beginner:** QUICK_START.md → RUN_DASHBOARD.md → Try dashboard

**Intermediate:** QUICK_REFERENCE.md → Build custom strategy → Test on dashboard

**Advanced:** STRATEGY_BUILDER_GUIDE.md → Nested logic → Complex strategies

**Expert:** CHANGES_SUMMARY.md → Code review → Extend functionality

---

## ✅ Checklist: Before You Start

- [ ] Python 3.8+ installed
- [ ] Virtual environment created (`.venv`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created (copy from `.env.example`)
- [ ] Read [QUICK_START.md](QUICK_START.md)

Then:
- [ ] Run `streamlit run dashboard/app.py`
- [ ] Open `http://localhost:8501`
- [ ] Go to Strategy Builder page
- [ ] Create and save a strategy
- [ ] Go to Run Screener page
- [ ] Test your strategy

---

## 🚀 You're Ready!

Pick your starting point above and follow the link. You'll be building strategies in minutes.

**Questions?** Everything is documented. No guessing needed!

---

**Happy strategizing!** 📈
