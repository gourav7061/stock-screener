# Run Screener

## Objective
Execute a saved strategy against the cached stock universe to shortlist matching stocks.

## Required Inputs
- **Strategy ID or name** (picked from saved strategies)
- **Market scope** (US, India, or Both)
- **Universe scope** (Full universe, Index only, or Custom pasted list)

## Tools Used
- **Dashboard UI** → `stockscreener/strategy_engine.py::run_strategy_against_db()`
- Database: `technicals_latest`, `fundamentals_latest`, `fundamentals` (for custom line items)

## Process
1. Load strategy definition (JSON)
2. Fetch applicable data from cache (technicals for all, fundamentals for those needed)
3. Evaluate strategy conditions recursively for each ticker
4. Collect passing tickers into result DataFrame
5. Export to CSV or view in-app

## Expected Output
- DataFrame with matching tickers and their metric values
- Download as CSV with timestamp
- Shows how many passed out of total screened

## Edge Cases & Handling

### Data Staleness
- **Check**: Last-refreshed timestamp from `data_refresh_log`
- **Banner**: Warn if price data > 7 days old (can configure `STALENESS_WARNING_DAYS`)
- **Remedy**: Run "Data Refresh" to update cache

### Custom Universe (pasted tickers)
- **Validation**: Tickers must exist in `companies` table (case-insensitive, but .NS/.BO suffixes must match)
- **If not found**: Skip silently (row is dropped from results)

### Strategy Using Fundamentals Not in Cache
- **Example**: Running "Oversold Value Pick" (PE ratio) if US fundamentals not yet fetched
- **Behavior**: Any missing fundamental value causes that ticker to be filtered out
- **Remedy**: Run "Data Refresh" → "US Fundamentals"

### No Matches
- **Result**: Empty DataFrame, message "❌ No stocks matched"
- **Reason**: Either filters are too tight, or data is not fresh
- **Remedy**: Loosen filters, or check data freshness

### Performance
- **Scanning 1000 stocks**: ~2-5 seconds (in-memory filtering, fast)
- **Scanning 10000 stocks**: ~10-30 seconds (still in-memory, but larger table)
- **Bottleneck**: Database query time, not evaluation time (all conditions are evaluated in Python)

## Typical Workflow
```
1. Go to Dashboard → Run Screener tab
2. Pick a strategy from dropdown
3. View its rules (human-readable)
4. Choose market + universe
5. Click "Run Screener"
6. See results, download CSV
7. Drill into a stock via "Fundamentals" tab for due diligence
```

## Strategic Tips
- **Use AND conditions** for precision (fewer results, higher quality)
- **Use OR conditions** for breadth (more results, some noise)
- **Combine technical + fundamental**: e.g., "Momentum (technical) + Valuation (fundamental)" for balanced picks
- **Test on a small universe first**: Custom list of 10-20 names you know, verify results make sense
- **Iterate**: Save multiple variants of a strategy, backtest which one would have worked historically (v2 feature)

## Verification
- Spot-check a result: Does the ticker really meet all conditions?
  - Pick one stock from results
  - Go to "Fundamentals" tab
  - Verify its values match the strategy conditions
- Check for false positives:
  - If a big-name stock is missing, it either doesn't meet criteria (double-check) or data is stale (refresh)

## Known Limitations (v1)
- **No backtesting**: Can't see how this strategy would have worked historically
- **No comparison**: Can't run multiple strategies and rank results by multiple factors
- **No alerts**: Can't set up recurring runs to email you results daily
- (All planned for v2+)
