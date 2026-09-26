# Review Fundamentals

## Objective
Analyze a stock's 10-year financial history to assess fundamental health and identify trends.

## Required Inputs
- **Ticker symbol** (US or India)
- **Optional**: Custom line items to track alongside standard metrics

## Tools Used
- Dashboard "Fundamentals" tab → Database: `fundamentals`, `fundamentals_latest`
- Chart rendering: Plotly (for trend visualization, v2+)

## Process
1. Pick a stock from dropdown
2. View available fundamental line items (revenue, EPS, ROE, debt, etc.)
3. Expand each to see up to 10 years of values
4. Spot trends (growing revenue but declining margins? Increasing debt?)
5. (v2+) Add custom line items from company filings to track

## Available Line Items (US & India)
- **Income Statement**: Revenue, Net Income, Operating Income, EPS, Profit Margin
- **Balance Sheet**: Total Assets, Liabilities, Equity, Debt, Shares Outstanding
- **Cash Flow**: Operating Cash Flow, Free Cash Flow
- **Ratios** (computed from above): P/E, P/B, Debt/Equity, ROE, Revenue Growth, Earnings Growth

## Edge Cases & Handling

### Stock Not in Coverage Tier
- **US stocks**: All tickers have `has_fundamentals=1` (full SEC EDGAR coverage)
- **India stocks**: Only Nifty500 + BSE500 have fundamentals (`has_fundamentals=1`). Other 4500+ India stocks are technicals-only.
  - **Message**: "⚠️ Fundamentals not available (outside coverage tier)"
  - **Reason**: No free comprehensive source for all 5000+ Indian stocks
  - **Workaround**: Upgrade to a paid API (Zerodha Kite, Tijori Finance) for full India coverage

### Missing Data for a Line Item
- **Reason**: Company didn't report it (rare), or data not yet fetched from source
- **Show**: Empty table under the expander
- **Remedy**: Run "Data Refresh" → "US Fundamentals" (for US) or wait for v2+ India fundamentals

### Non-Standard Fiscal Periods
- **US**: Most calendar year-end (Dec 31), but some fiscal year-end
- **India**: Fiscal year is April–March (different from calendar year)
- **Display**: All dates in ISO format (YYYY-MM-DD) for clarity

## Typical Analysis Workflow

### Example 1: Value Investor Deep Dive
1. Screen for low P/E + high ROE → get shortlist (via "Run Screener")
2. Pick one from results
3. Go to "Fundamentals" tab
4. Expand Revenue, Net Income, EPS over 10 years
   - Is revenue growing steadily?
   - Is income growing faster than revenue (operating leverage)?
5. Expand Debt/Equity
   - Is debt stable/declining?
6. Expand Free Cash Flow
   - Can company fund dividends + growth from cash?

### Example 2: Growth Investor Trend Check
1. Screen for revenue growth > 20% → shortlist
2. Review Fundamentals:
3. Revenue trend (up consistently?)
4. EPS trend (earnings keeping up with sales?)
5. Margin trend (is unit economics improving or declining?)
6. Cash flow (can they fund growth organically?)

### Example 3: Risk Check Before Buying
1. Review balance sheet health:
   - Total Debt vs. Market Cap (is leverage excessive?)
   - Current Assets vs. Current Liabilities (can they pay short-term obligations?)
2. Review profitability:
   - Net Margin trend (stable or declining?)
   - ROE trend (is management deploying capital effectively?)
3. Review growth:
   - Revenue CAGR over 3, 5, 10 years (what's the growth story?)

## Custom Line Items (v2 Feature)
In v1, you see standard line items only. v2 will let you:
- Add custom metrics from company filings
- Example: "R&D Spend as % of Revenue" (track whether a tech company is investing enough)
- Example: "Interest Coverage Ratio" (can company service debt?)
- Example: "Working Capital Turnover" (how efficiently using assets?)

## Verification
- Pick one company, one line item
- Go to SEC EDGAR's website (us-ceo.sec.gov) or Screener.in for India
- Spot-check one year's value matches what's shown in the app
- Verify the source matches (SEC_EDGAR vs. SCREENER_IN)

## Known Limitations (v1)
- **No interactive charts**: Can't zoom/pan trend charts (v2+ with Plotly)
- **No peer comparison**: Can't compare company's metrics against industry average
- **No multi-year ratios**: Some ratios (e.g., 5-yr CAGR) computed on-demand; not pre-cached
- **No forecasting**: Can't predict future values based on historical trends
- (All planned for v2+)

## Data Sources
- **US**: SEC EDGAR XBRL filings (quarterly 10-Q and annual 10-K)
- **India**: 
  - v1: Not available (Nifty500/BSE500 tier requires external scraping)
  - v2+: NSE XBRL filings or paid API
