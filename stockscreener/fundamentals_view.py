"""Read-side query + formatting helpers for the Fundamentals page.

Pulls together `fundamentals`, `fundamentals_latest`, and `shareholding_pattern`
(populated by screener_in.py) into the four sections the Fundamentals page shows:
Ratios, Profit & Loss, Cash Flow, Shareholding Pattern.
"""

import re
import sqlite3
from typing import Dict, List, Optional, Tuple

import pandas as pd

_ANNUAL_PERIOD_RE = re.compile(r"^FY\d{4}$")
_QUARTERLY_PERIOD_RE = re.compile(r"^Q\dFY\d{2}$")

# Ratios that need real historical series / peer data we don't have a source for yet.
# Shown in the UI as "Not available yet" with this reason rather than a guessed number.
UNAVAILABLE_RATIOS = {
    "CMP / FCF": "Free Cash Flow needs a CapEx breakout Screener.in doesn't expose on the main page",
    "Intrinsic Value": "Needs a chosen valuation methodology (DCF, Graham, etc.) — not a scraped fact",
    "EV/EBITDA": "Needs cash & equivalents + D&A breakout not captured from the current scrape",
    "5Yrs PE": "Needs a historical price-vs-EPS join across 5 fiscal years — not built yet",
    "ROCE 3yr avg": "Only the current ROCE is scraped; historical ROCE series isn't captured yet",
    "Industry PE": "Needs a peer/sector comparison data source — not available",
    "ROIC": "Needs a reliable invested-capital figure (cash breakout not captured) — not available",
}


def _fmt(value, decimals=2, suffix="") -> Optional[str]:
    if value is None:
        return None
    return f"{value:,.{decimals}f}{suffix}"


def get_ratios_snapshot(con: sqlite3.Connection, ticker: str) -> Dict[str, dict]:
    """Return the Ratios section as {label: {"value": str|None, "available": bool, "reason": str|None}}."""
    cursor = con.cursor()
    cursor.execute("SELECT * FROM fundamentals_latest WHERE ticker = ?", (ticker,))
    row = cursor.fetchone()
    latest = dict(row) if row else {}

    items = {
        "Market Cap": _fmt(latest.get("market_cap"), 0, " Cr"),
        "Current Price": _fmt(latest.get("current_price")),
        "52 week High / Low": (
            f"{_fmt(latest.get('high_52w'))} / {_fmt(latest.get('low_52w'))}"
            if latest.get("high_52w") is not None and latest.get("low_52w") is not None else None
        ),
        "Stock P/E": _fmt(latest.get("pe_ratio")),
        "Book Value": _fmt(latest.get("book_value")),
        "ROCE": _fmt(latest.get("roce"), 1, "%"),
        "ROE": _fmt(latest.get("roe"), 1, "%"),
        "Price to Book Value": _fmt(latest.get("pb_ratio")),
        "Debt to Equity": _fmt(latest.get("debt_to_equity")),
        "Debt": _fmt(latest.get("debt"), 0, " Cr"),
    }

    cash_conversion = _compute_cash_conversion_ratio(con, ticker)
    items["Cash Conversion Ratio"] = _fmt(cash_conversion) if cash_conversion is not None else None

    peg = _compute_peg_ratio(con, ticker, latest.get("pe_ratio"))
    items["PEG Ratio"] = _fmt(peg) if peg is not None else None

    result = {}
    for label, value in items.items():
        result[label] = {"value": value, "available": value is not None, "reason": None}

    for label, reason in UNAVAILABLE_RATIOS.items():
        result[label] = {"value": None, "available": False, "reason": reason}

    return result


def _latest_two_annual_values(con: sqlite3.Connection, ticker: str, line_item_key: str) -> List[Tuple[str, float]]:
    cursor = con.cursor()
    cursor.execute("""
        SELECT fiscal_period, value FROM fundamentals
        WHERE ticker = ? AND line_item_key = ? AND fiscal_period LIKE 'FY%'
        ORDER BY fiscal_period DESC LIMIT 2
    """, (ticker, line_item_key))
    return cursor.fetchall()


def _compute_cash_conversion_ratio(con: sqlite3.Connection, ticker: str) -> Optional[float]:
    """CFO / Net Profit for the most recent fiscal year both are available for."""
    cursor = con.cursor()
    cursor.execute("""
        SELECT cfo.value, np.value FROM fundamentals cfo
        JOIN fundamentals np ON np.ticker = cfo.ticker AND np.fiscal_period = cfo.fiscal_period
        WHERE cfo.ticker = ? AND cfo.line_item_key = 'operating_cash_flow'
          AND np.line_item_key = 'net_income' AND cfo.fiscal_period LIKE 'FY%'
        ORDER BY cfo.fiscal_period DESC LIMIT 1
    """, (ticker,))
    row = cursor.fetchone()
    if not row or not row[1]:
        return None
    return row[0] / row[1]


def _compute_peg_ratio(con: sqlite3.Connection, ticker: str, pe_ratio: Optional[float]) -> Optional[float]:
    """PEG = Stock P/E / YoY EPS growth %, using the two most recent fiscal years' EPS."""
    if not pe_ratio:
        return None
    rows = _latest_two_annual_values(con, ticker, "eps_diluted")
    if len(rows) < 2:
        return None
    (_, latest_eps), (_, prev_eps) = rows
    if not prev_eps:
        return None
    growth_pct = (latest_eps - prev_eps) / abs(prev_eps) * 100
    if growth_pct <= 0:
        return None
    return pe_ratio / growth_pct


_PL_ROWS = [
    ("revenue", "Revenue", 0, ""),
    ("operating_profit_pct", "Operating Profit %", 1, "%"),
    ("net_income", "Net Profit", 0, ""),
    ("eps_diluted", "EPS", 2, ""),
]


def _period_column_label(fiscal_period: str, period_end_date: Optional[str]) -> str:
    if fiscal_period == "TTM":
        return "TTM"
    if period_end_date:
        year, month = period_end_date[:4], period_end_date[5:7]
        month_abbr = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
                     "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"}[month]
        return f"{month_abbr}'{year[2:]}"
    return fiscal_period


def get_pl_table(con: sqlite3.Connection, ticker: str, period_type: str,
                 max_periods: int = 8) -> pd.DataFrame:
    """period_type: 'annual' (last 5 years + TTM) or 'quarterly' (last N quarters)."""
    cursor = con.cursor()
    line_item_keys = [k for k, _, _, _ in _PL_ROWS]
    placeholders = ",".join(["?" for _ in line_item_keys])
    cursor.execute(f"""
        SELECT fiscal_period, period_end_date, line_item_key, value FROM fundamentals
        WHERE ticker = ? AND line_item_key IN ({placeholders})
    """, [ticker] + line_item_keys)
    rows = cursor.fetchall()

    period_pattern = _ANNUAL_PERIOD_RE if period_type == "annual" else _QUARTERLY_PERIOD_RE
    by_period = {}
    for fiscal_period, period_end_date, key, value in rows:
        is_ttm = period_type == "annual" and fiscal_period == "TTM"
        if not (period_pattern.match(fiscal_period) or is_ttm):
            continue
        sort_key = "9999-99-99" if fiscal_period == "TTM" else (period_end_date or fiscal_period)
        by_period.setdefault(sort_key, {"fiscal_period": fiscal_period, "period_end_date": period_end_date})
        by_period[sort_key][key] = value

    sorted_keys = sorted(by_period.keys())
    n = 5 if period_type == "annual" else max_periods
    # Keep TTM (sorts last) plus the most recent n-1 real periods before it, or just the last n.
    ttm_key = "9999-99-99"
    non_ttm_keys = [k for k in sorted_keys if k != ttm_key]
    kept_keys = non_ttm_keys[-(n - 1 if ttm_key in sorted_keys else n):]
    if ttm_key in sorted_keys:
        kept_keys.append(ttm_key)

    columns = [_period_column_label(by_period[k]["fiscal_period"], by_period[k]["period_end_date"])
              for k in kept_keys]

    data = {}
    for line_item_key, label, decimals, suffix in _PL_ROWS:
        data[label] = [
            _fmt(by_period[k].get(line_item_key), decimals, suffix) or "-" for k in kept_keys
        ]

    return pd.DataFrame(data, index=columns).T


_CF_ROWS = [
    ("operating_cash_flow", "Cash from Operating Activity +"),
    ("investing_cash_flow", "Cash from Investing Activity +"),
    ("financing_cash_flow", "Cash from Financing Activity +"),
    ("net_cash_flow", "Net Cash Flow"),
]


def get_cash_flow_table(con: sqlite3.Connection, ticker: str,
                        period_type: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Returns (df, note). India companies only disclose cash flow annually, so a
    'quarterly' request returns (None, explanation) instead of an empty table."""
    if period_type == "quarterly":
        return None, "India companies disclose cash flow annually only — no quarterly cash flow statement exists."

    cursor = con.cursor()
    keys = [k for k, _ in _CF_ROWS] + ["operating_profit"]
    placeholders = ",".join(["?" for _ in keys])
    cursor.execute(f"""
        SELECT fiscal_period, period_end_date, line_item_key, value FROM fundamentals
        WHERE ticker = ? AND line_item_key IN ({placeholders}) AND fiscal_period LIKE 'FY%'
    """, [ticker] + keys)
    rows = cursor.fetchall()

    by_period = {}
    for fiscal_period, period_end_date, key, value in rows:
        by_period.setdefault(period_end_date, {"fiscal_period": fiscal_period, "period_end_date": period_end_date})
        by_period[period_end_date][key] = value

    sorted_keys = sorted(k for k in by_period if k)[-5:]
    columns = [_period_column_label(by_period[k]["fiscal_period"], k) for k in sorted_keys]

    data = {}
    for line_item_key, label in _CF_ROWS:
        data[label] = [_fmt(by_period[k].get(line_item_key), 0) or "-" for k in sorted_keys]

    cfo_to_op = []
    for k in sorted_keys:
        cfo = by_period[k].get("operating_cash_flow")
        op = by_period[k].get("operating_profit")
        cfo_to_op.append(_fmt(cfo / op, 2) if cfo is not None and op else "-")
    data["CFO/OP"] = cfo_to_op
    data["Free Cash Flow"] = ["N/A"] * len(sorted_keys)

    return pd.DataFrame(data, index=columns).T, None


_SHP_ROWS = [
    ("promoter_pct", "Promoter"),
    ("fii_pct", "FIIs"),
    ("dii_pct", "DIIs"),
    ("others_pct", "Others"),
]


def get_shareholding_table(con: sqlite3.Connection, ticker: str, period_type: str,
                           max_periods: int = 8) -> pd.DataFrame:
    """period_type: 'annual' (March fiscal-year-end snapshots) or 'quarterly' (all disclosed quarters)."""
    cursor = con.cursor()
    if period_type == "annual":
        cursor.execute("""
            SELECT period_end_date, period_label, promoter_pct, fii_pct, dii_pct, others_pct
            FROM shareholding_pattern WHERE ticker = ? AND period_end_date LIKE '%-03-31'
            ORDER BY period_end_date DESC LIMIT 5
        """, (ticker,))
    else:
        cursor.execute("""
            SELECT period_end_date, period_label, promoter_pct, fii_pct, dii_pct, others_pct
            FROM shareholding_pattern WHERE ticker = ?
            ORDER BY period_end_date DESC LIMIT ?
        """, (ticker, max_periods))

    rows = cursor.fetchall()[::-1]  # chronological order
    columns = [r[1] for r in rows]

    data = {}
    for idx, (_, label) in enumerate(_SHP_ROWS):
        data[label] = [_fmt(r[2 + idx], 2, "%") or "-" for r in rows]

    return pd.DataFrame(data, index=columns).T


def has_india_fundamentals(con: sqlite3.Connection, ticker: str) -> bool:
    cursor = con.cursor()
    cursor.execute("SELECT 1 FROM fundamentals_latest WHERE ticker = ?", (ticker,))
    return cursor.fetchone() is not None
