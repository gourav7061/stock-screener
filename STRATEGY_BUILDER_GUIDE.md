# Flexible Strategy Builder Guide

Your stock screening strategy builder now supports **unlimited, custom conditions** with AND/OR logic. No more fixed sets of conditions—you define exactly what you need.

## Quick Start: Define Your First Strategy

### 1. Choose Your Metrics

Available metrics are organized by category:

**Moving Averages:**
- `sma20`, `sma50`, `sma150`, `sma200`, `sma220` (Simple Moving Averages)
- `ema220` (Exponential Moving Average)

**Price & Support/Resistance:**
- `price` (current price)
- `52w_low` (52-week low)
- `52w_low_25pct` (52-week low × 1.25)
- `pct_from_52w_high`, `pct_from_52w_low` (percentage metrics)

**Momentum:**
- `rsi14` (Relative Strength Index)
- `macd`, `macd_signal`, `macd_hist`

**Volatility:**
- `bb_upper`, `bb_lower`, `bb_mid` (Bollinger Bands)
- `bb_percent_b`

**Volume:**
- `volume`, `avg_volume_20d`, `volume_spike_ratio`

**Price Change:**
- `pct_change_1d`, `pct_change_1m`, `pct_change_3m`, `pct_change_1y`

**Fundamentals:**
- `pe_ratio`, `forward_pe`, `pb_ratio`, `debt_to_equity`, `roe`, `profit_margin`, `revenue_growth`, `earnings_growth`, `dividend_yield`, `market_cap`

---

## 2. Define Conditions

### Pattern 1: Simple Comparison (Metric vs Value)

Compare a single metric to a fixed number.

```json
{
  "metric": "price",
  "operator": ">",
  "compare_type": "value",
  "value": 100.0
}
```

**Operators:** `>`, `<`, `>=`, `<=`, `==`, `!=`

**Real-world example:** "Price is above $100"

---

### Pattern 2: Metric-to-Metric Comparison

Compare two metrics against each other.

```json
{
  "metric": "sma50",
  "operator": ">",
  "compare_type": "metric",
  "compare_metric": "sma200"
}
```

**Real-world example:** "50-day SMA above 200-day SMA (golden cross)"

---

### Pattern 3: Historical Dip Detection

Check if a stock **touched or dipped below a level** in the past N trading days.

```json
{
  "condition_type": "dipped_below",
  "compare_level": "ema220",
  "days": 90
}
```

**Real-world example:** "Stock touched 220-day EMA in the last 90 days (confirms support test)"

---

## 3. Combine Conditions with Logic

### All conditions must pass (AND)

```json
{
  "root": {
    "logic": "AND",
    "items": [
      { "metric": "price", "operator": ">", "compare_type": "value", "value": 50.0 },
      { "metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma200" },
      { "metric": "rsi14", "operator": "<", "compare_type": "value", "value": 70.0 }
    ]
  }
}
```

Result: Stock must be **above $50 AND** have a golden cross **AND** not be overbought.

---

### Any condition can pass (OR)

```json
{
  "root": {
    "logic": "OR",
    "items": [
      { "metric": "pct_change_1m", "operator": ">", "compare_type": "value", "value": 10.0 },
      { "metric": "pct_change_3m", "operator": ">", "compare_type": "value", "value": 15.0 }
    ]
  }
}
```

Result: Stock is up **>10% in 1 month OR >15% in 3 months**.

---

### Nested Logic (Complex Strategies)

```json
{
  "root": {
    "logic": "AND",
    "items": [
      {
        "metric": "price",
        "operator": ">",
        "compare_type": "metric",
        "compare_metric": "sma50"
      },
      {
        "logic": "OR",
        "items": [
          { "metric": "rsi14", "operator": "<", "compare_type": "value", "value": 40.0 },
          { "metric": "pct_change_1m", "operator": "<", "compare_type": "value", "value": -5.0 }
        ]
      }
    ]
  }
}
```

Result: Price above 50-day SMA **AND** (RSI is oversold **OR** down >5% in 1 month).

---

## Complete Example: 220 EMA Breakout

Here's the exact strategy from your screenshot:

```json
{
  "name": "220 EMA Breakout",
  "root": {
    "logic": "AND",
    "items": [
      {
        "condition_type": "description",
        "text": "1. 150 SMA > 220 EMA (medium-term above long-term)"
      },
      {
        "metric": "sma150",
        "operator": ">",
        "compare_type": "metric",
        "compare_metric": "ema220"
      },
      {
        "condition_type": "description",
        "text": "2. Price > 50 SMA (in uptrend)"
      },
      {
        "metric": "price",
        "operator": ">",
        "compare_type": "metric",
        "compare_metric": "sma50"
      },
      {
        "condition_type": "description",
        "text": "3. 50 SMA > 150 SMA (shorter-term leading)"
      },
      {
        "metric": "sma50",
        "operator": ">",
        "compare_type": "metric",
        "compare_metric": "sma150"
      },
      {
        "condition_type": "description",
        "text": "4. Price > 125% of 52-week low (25% above support)"
      },
      {
        "metric": "price",
        "operator": ">",
        "compare_type": "metric",
        "compare_metric": "52w_low_25pct"
      },
      {
        "condition_type": "description",
        "text": "5. Dipped below 220 EMA in past 90 days (confirmed support test)"
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

**What this does:**
✓ Identifies stocks in a healthy uptrend  
✓ Confirms multiple moving average alignments  
✓ Ensures recovery from recent support (220 EMA touch)  
✓ Validates breakout above 52-week support level

---

## How to Use (Code)

### Define a Strategy

```python
from stockscreener.strategy_engine import save_strategy, validate_strategy, run_strategy_against_db
from stockscreener.db import get_connection
from stockscreener.metrics import get_metrics_registry

strategy = {
    "name": "My Custom Strategy",
    "root": {
        "logic": "AND",
        "items": [
            # Your conditions here
        ]
    }
}

con = get_connection()
metrics = get_metrics_registry(con)

# Validate it first
errors = validate_strategy(strategy, metrics)
if errors:
    print("Errors:", errors)
else:
    # Save to database
    strategy_id = save_strategy(con, strategy)
    print(f"Strategy #{strategy_id} saved!")
```

### Run a Strategy

```python
# Get the strategy you saved
from stockscreener.strategy_engine import load_strategy

strategy = load_strategy(con, strategy_id=1)

# Run it against a list of tickers
tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
results = run_strategy_against_db(con, strategy, tickers)

print(results)  # DataFrame of matching stocks
```

### Use the Built-in Examples

```bash
# Show available metrics
python tools/example_strategies.py --list-metrics

# Show syntax guide
python tools/example_strategies.py --syntax

# Save example strategies to database
python tools/example_strategies.py --save
```

---

## Validation Rules

Strategies are validated to ensure they're correct:

1. ✓ Name is required and unique
2. ✓ Must have a root node (AND or OR group)
3. ✓ All metric keys must exist
4. ✓ Operators must be: `>`, `<`, `>=`, `<=`, `==`, `!=`
5. ✓ Nesting depth limited to 5 levels (to avoid complexity)
6. ✓ Groups must have at least one item

---

## Advanced Patterns

### Trend Confirmation (Multiple Timeframes)

```json
{
  "logic": "AND",
  "items": [
    { "metric": "pct_change_1m", "operator": ">", "compare_type": "value", "value": 5.0 },
    { "metric": "pct_change_3m", "operator": ">", "compare_type": "value", "value": 10.0 },
    { "metric": "pct_change_1y", "operator": ">", "compare_type": "value", "value": 20.0 }
  ]
}
```

**Result:** Strong uptrend confirmed across 1-month, 3-month, and 1-year timeframes.

---

### Quality + Value (Combine Technical + Fundamental)

```json
{
  "logic": "AND",
  "items": [
    { "metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma200" },
    { "metric": "pe_ratio", "operator": "<", "compare_type": "value", "value": 20.0 },
    { "metric": "roe", "operator": ">", "compare_type": "value", "value": 15.0 }
  ]
}
```

**Result:** In an uptrend AND trading at reasonable valuation AND profitable (good ROE).

---

### Mean Reversion Setup

```json
{
  "logic": "AND",
  "items": [
    { "metric": "rsi14", "operator": "<", "compare_type": "value", "value": 30.0 },
    { "metric": "pct_change_1m", "operator": "<", "compare_type": "value", "value": -10.0 },
    { "metric": "bb_percent_b", "operator": "<", "compare_type": "value", "value": 0.2 }
  ]
}
```

**Result:** Oversold (RSI < 30) after decline (down >10%) and near lower Bollinger Band.

---

## Troubleshooting

### "Unknown metric: xyz"
→ Check the metric name in `--list-metrics`. Metrics are case-sensitive and use underscores.

### "Invalid compare_metric: abc"
→ The metric you're comparing to doesn't exist. Verify both metric names.

### "Strategy nesting exceeds maximum depth"
→ You've nested groups more than 5 levels deep. Simplify or use additional strategies instead.

### Strategy validates but doesn't match any stocks
→ This is normal! Your conditions may be too strict. Try:
- Loosening numerical thresholds
- Using OR instead of AND for some conditions
- Removing the "dipped_below" condition (requires recent support test)

---

## Next Steps

1. **List metrics**: `python tools/example_strategies.py --list-metrics`
2. **View examples**: `python tools/example_strategies.py --syntax`
3. **Define your strategy** in JSON format
4. **Validate** it before saving
5. **Test** against a few tickers before running the full screener
6. **Iterate** as you refine your trading rules

Happy screening!
