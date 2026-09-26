# Define Strategy

## Objective
Build a no-code screening strategy with AND/OR conditions, save it for later execution.

## Required Inputs
- **Strategy name** (string, unique)
- **At least 1 condition** (metric + operator + compare-to value/metric)
- **Logic** (AND all conditions, or OR them)

## Tools Used
- **Dashboard UI** → `stockscreener/strategy_engine.py` for validation and storage
- Database: `strategies` table (ID, name, definition_json)

## Condition Schema
Each condition is:
```json
{
  "metric": "pe_ratio|rsi14|sma50|...",
  "operator": ">|<|>=|<=|==|!=",
  "compare_type": "value|metric",
  "value": 25.0,
  "compare_metric": "sma200"  // only used if compare_type="metric"
}
```

## Available Metrics
- **Technical** (price/chart-based): `price`, `sma20`, `sma50`, `sma150`, `sma200`, `sma220`, `ema220`, `rsi14`, `macd`, `macd_signal`, `macd_hist`, `bb_upper`, `bb_lower`, `bb_percent_b`, `pct_change_1d/1m/3m/1y`, `pct_from_52w_high/low`, `52w_low`, `52w_low_25pct`, `volume`, `avg_volume_20d`, `volume_spike_ratio`
- **Fundamental** (financial ratios): `pe_ratio`, `forward_pe`, `pb_ratio`, `debt_to_equity`, `roe`, `profit_margin`, `revenue_growth`, `earnings_growth`, `dividend_yield`, `market_cap`
- **Custom** (user-added): Any custom line items registered in `custom_line_items` table

## Strategy Persistence
- **Format**: Recursive JSON tree (AND/OR groups containing conditions)
- **Storage**: SQLite `strategies` table
- **Access**: Via dashboard "Strategy Builder" page or direct SQL queries

## Migration from Prototype
**Legacy v0 schema** (flat AND-only):
```json
{"name": "...", "conditions": [{...}, {...}]}
```

**New v1 schema** (recursive AND/OR):
```json
{
  "name": "...",
  "root": {
    "logic": "AND",
    "items": [
      {"metric": "sma50", "operator": ">", ...},
      {"logic": "OR", "items": [...]}  // nested groups, v2+
    ]
  }
}
```

Tool: `tools/migrate_legacy_strategies.py` converts old to new.

## Validation Rules
1. Strategy must have a non-empty name
2. Must have a root node (AND or OR)
3. Groups must contain at least one item
4. All metric keys must exist in the metrics registry
5. Operators must be one of: `>`, `<`, `>=`, `<=`, `==`, `!=`
6. If `compare_type="metric"`, the compare_metric must be a valid key
7. Max nesting depth: 5 levels (to avoid UI complexity)

## Examples

### Example 1: "220 EMA Breakout"
**Conditions:**
1. 150-day SMA > 220-day EMA
2. Current Price > 50-day SMA
3. 50-day SMA > 150-day SMA
4. Price > 125% of 52-week Low (25% above low)
5. Stock dipped below 220 EMA at least once in past 90 trading days

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

### Example 2: "Golden Cross Momentum"
Condition: SMA50 > SMA200 AND Current Price > SMA50 AND 1-Month % Change > 3%
```json
{
  "name": "Golden Cross Momentum",
  "root": {
    "logic": "AND",
    "items": [
      {"metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma200"},
      {"metric": "price", "operator": ">", "compare_type": "metric", "compare_metric": "sma50"},
      {"metric": "pct_change_1m", "operator": ">", "compare_type": "value", "value": 3.0}
    ]
  }
}
```

### Example 3: "Oversold Value Pick"
Condition: RSI < 35 AND P/E < 25
```json
{
  "name": "Oversold Value Pick",
  "root": {
    "logic": "AND",
    "items": [
      {"metric": "rsi14", "operator": "<", "compare_type": "value", "value": 35.0},
      {"metric": "pe_ratio", "operator": "<", "compare_type": "value", "value": 25.0}
    ]
  }
}
```

## Special Condition Types

### Simple Comparison (Default)
Compare a metric to a static value or another metric.
```json
{
  "metric": "price",
  "operator": ">",
  "compare_type": "value",
  "value": 100.5
}
```

### Metric-to-Metric Comparison
Compare two metrics against each other.
```json
{
  "metric": "sma50",
  "operator": ">",
  "compare_type": "metric",
  "compare_metric": "sma200"
}
```

### Historical Dip Detection
Check if price dipped below a threshold in the past N trading days.
```json
{
  "condition_type": "dipped_below",
  "compare_level": "ema220",
  "days": 90
}
```
This is useful for entry signals where you want to confirm the stock recently tested support.

## How to Use (Programmatically)

```python
from stockscreener.db import get_connection
from stockscreener.strategy_engine import save_strategy, validate_strategy

# Define your strategy
strategy = {
  "name": "My Strategy",
  "root": {
    "logic": "AND",
    "items": [
      # Add your conditions here
    ]
  }
}

# Validate (optional, but recommended)
con = get_connection()
errors = validate_strategy(strategy, get_metrics_registry(con))
if errors:
  print("Strategy has errors:", errors)
else:
  # Save to database
  strategy_id = save_strategy(con, strategy)
  print(f"Strategy saved with ID: {strategy_id}")
```

See `tools/example_strategies.py` for complete examples and usage patterns.

## Future Enhancements (v2+)
- **Full AND/OR nesting**: Build arbitrary nested groups via UI
- **Custom metrics**: Add/compute derived metrics (e.g., "Revenue / Market Cap")
- **Backtesting**: Run strategy against historical data to see how picks would have performed
- **Strategy templates**: Pre-built common strategies (value, growth, momentum, quality)
- **Sharing**: Export/import strategies as JSON for team sharing
