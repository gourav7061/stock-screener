# Strategy Builder Quick Reference

## 3-Step Strategy Definition

### Step 1: Define Individual Conditions

**Metric vs Static Value:**
```json
{"metric": "price", "operator": ">", "compare_type": "value", "value": 100.0}
```

**Metric vs Metric:**
```json
{"metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma200"}
```

**Historical Dip (past N days):**
```json
{"condition_type": "dipped_below", "compare_level": "ema220", "days": 90}
```

### Step 2: Combine with Logic

```json
{
  "root": {
    "logic": "AND",  // or "OR"
    "items": [
      { condition1 },
      { condition2 },
      { condition3 }
    ]
  }
}
```

### Step 3: Add Name & Save

```python
from stockscreener.strategy_engine import save_strategy
from stockscreener.db import get_connection

strategy = {
    "name": "My Strategy",
    "root": { /* from Step 2 */ }
}

con = get_connection()
strategy_id = save_strategy(con, strategy)
```

---

## Available Metrics Cheat Sheet

| Category | Metrics |
|----------|---------|
| **Moving Averages** | `sma20`, `sma50`, `sma150`, `sma200`, `sma220`, `ema220` |
| **Price Support** | `price`, `52w_low`, `52w_low_25pct` |
| **Price % Change** | `pct_from_52w_high`, `pct_from_52w_low`, `pct_change_1d`, `pct_change_1m`, `pct_change_3m`, `pct_change_1y` |
| **Momentum** | `rsi14`, `macd`, `macd_signal`, `macd_hist` |
| **Volatility** | `bb_upper`, `bb_lower`, `bb_mid`, `bb_percent_b` |
| **Volume** | `volume`, `avg_volume_20d`, `volume_spike_ratio` |
| **Fundamentals** | `pe_ratio`, `forward_pe`, `pb_ratio`, `debt_to_equity`, `roe`, `profit_margin`, `revenue_growth`, `earnings_growth`, `dividend_yield`, `market_cap` |

---

## Operators

```
>   greater than
<   less than
>=  greater than or equal
<=  less than or equal
==  equal
!=  not equal
```

---

## Common Patterns

### Golden Cross
```json
{
  "logic": "AND",
  "items": [
    {"metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma200"},
    {"metric": "price", "operator": ">", "compare_type": "metric", "compare_metric": "sma50"}
  ]
}
```

### Oversold + Cheap
```json
{
  "logic": "AND",
  "items": [
    {"metric": "rsi14", "operator": "<", "compare_type": "value", "value": 35.0},
    {"metric": "pe_ratio", "operator": "<", "compare_type": "value", "value": 20.0}
  ]
}
```

### Either/Or Entry
```json
{
  "logic": "OR",
  "items": [
    {"metric": "pct_change_1m", "operator": ">", "compare_type": "value", "value": 10.0},
    {"metric": "rsi14", "operator": "<", "compare_type": "value", "value": 30.0}
  ]
}
```

### Complex Nested
```json
{
  "logic": "AND",
  "items": [
    {"metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma200"},
    {
      "logic": "OR",
      "items": [
        {"metric": "rsi14", "operator": "<", "compare_type": "value", "value": 40.0},
        {"metric": "pct_change_1m", "operator": "<", "compare_type": "value", "value": -5.0}
      ]
    }
  ]
}
```

---

## Full Example: 220 EMA Breakout

```python
from stockscreener.strategy_engine import save_strategy
from stockscreener.db import get_connection

strategy = {
    "name": "220 EMA Breakout",
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

con = get_connection()
strategy_id = save_strategy(con, strategy)
print(f"Strategy saved: ID {strategy_id}")
```

---

## Run & Test

```python
from stockscreener.strategy_engine import load_strategy, run_strategy_against_db

# Load your strategy
strategy = load_strategy(con, strategy_id=1)

# Test on a few tickers
test_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
results = run_strategy_against_db(con, strategy, test_tickers)

print(results)  # DataFrame with matching stocks
```

---

## CLI Commands

```bash
# See all metrics
python tools/example_strategies.py --list-metrics

# See syntax guide
python tools/example_strategies.py --syntax

# Save example strategies to database
python tools/example_strategies.py --save
```

---

## Quick Checklist

- [ ] Strategy has a unique name
- [ ] root node is "AND" or "OR"
- [ ] All metrics exist (use `--list-metrics` to verify)
- [ ] All operators are valid: > < >= <= == !=
- [ ] If using "metric" compare_type, compare_metric also exists
- [ ] If using "dipped_below", compare_level exists
- [ ] Nesting is ≤ 5 levels deep
- [ ] Tested on small ticker universe first

---

**That's it! You now have unlimited, flexible conditions.** 🎯
