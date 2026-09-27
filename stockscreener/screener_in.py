"""Screener.in scraping for India fundamentals (Ratios, P&L, Balance Sheet, Cash Flow,
Shareholding Pattern).

Screener.in page structure (as of 2026): a company page at
/company/<SYMBOL>/consolidated/ has fixed section ids we rely on:
  #top-ratios     - current point-in-time ratios (Market Cap, CMP, P/E, ROE, ...)
  #quarters       - quarterly P&L, one column per quarter
  #profit-loss    - annual P&L, one column per fiscal year + a final TTM column
  #balance-sheet  - annual balance sheet (used for Debt / Net Worth)
  #cash-flow      - annual cash flow (India discloses cash flow annually only, never quarterly)
  #shareholding   - #quarterly-shp and #yearly-shp tables (Promoters/FIIs/DIIs/Government/Public)

This is a real scrape of a third-party site with no public API: page structure changes
will break parsing silently (rows just won't be found). If a company's numbers stop showing
up, check SCREENER_STRUCTURE_NOTES below before assuming the data itself is missing.
"""

import logging
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from .config import SCREENER_IN_BASE_URL, SCREENER_IN_REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}

# Row label (as it appears on the page) -> our line_item_key. Keys reuse the same
# names as US_GAAP_MAP in sec_edgar.py where the concept matches, so the same
# strategy_engine metric works across both markets.
_QUARTERS_ROW_MAP = {
    "Sales": "revenue",
    "Operating Profit": "operating_profit",
    "OPM %": "operating_profit_pct",
    "Net Profit": "net_income",
    "EPS in Rs": "eps_diluted",
}
_PROFIT_LOSS_ROW_MAP = _QUARTERS_ROW_MAP
_BALANCE_SHEET_ROW_MAP = {
    "Equity Capital": "equity_capital",
    "Reserves": "reserves",
    "Borrowings": "debt",
    "Total Assets": "total_assets",
    "Total Liabilities": "total_liabilities",
}
_CASH_FLOW_ROW_MAP = {
    "Cash from Operating Activity": "operating_cash_flow",
    "Cash from Investing Activity": "investing_cash_flow",
    "Cash from Financing Activity": "financing_cash_flow",
    "Net Cash Flow": "net_cash_flow",
}
_SHAREHOLDING_ROW_MAP = {
    "Promoters": "promoter_pct",
    "FIIs": "fii_pct",
    "DIIs": "dii_pct",
}

_MONTH_NUM = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
    "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
}


def _clean_number(text: str) -> Optional[float]:
    """Parse a Screener.in table cell like '1,226', '22.2%', '-', '' into a float."""
    if text is None:
        return None
    text = text.strip().replace(",", "").replace("%", "").replace("₹", "").strip()
    if text in ("", "-", "—"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _india_fiscal_period_label(end_date_iso: str) -> str:
    """India fiscal year runs Apr-Mar. Given a quarter-end date, return e.g. 'Q1FY26'
    for a quarter ending Jun 2025 (FY2026 = Apr 2025 - Mar 2026)."""
    year, month = int(end_date_iso[:4]), int(end_date_iso[5:7])
    if month in (4, 5, 6):
        quarter, fy_end_year = 1, year + 1
    elif month in (7, 8, 9):
        quarter, fy_end_year = 2, year + 1
    elif month in (10, 11, 12):
        quarter, fy_end_year = 3, year + 1
    else:  # Jan, Feb, Mar
        quarter, fy_end_year = 4, year
    return f"Q{quarter}FY{str(fy_end_year)[2:]}"


def fetch_company_page(nse_symbol: str, consolidated: bool = True) -> str:
    """Fetch the raw HTML of a company's Screener.in page. Raises on HTTP error."""
    variant = "consolidated" if consolidated else ""
    url = f"{SCREENER_IN_BASE_URL}/company/{nse_symbol}/{variant}/".replace("//", "/").replace(":/", "://")
    response = requests.get(url, headers=_HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def parse_top_ratios(html: str) -> Dict[str, float]:
    """Parse the #top-ratios list into {label: value}. Units (₹, %, Cr.) are stripped —
    Market Cap and Debt are in Rs. Crores, prices/Book Value in Rs., ROE/ROCE/Dividend
    Yield in %."""
    soup = BeautifulSoup(html, "lxml")
    container = soup.find(id="top-ratios")
    if not container:
        return {}

    ratios = {}
    for li in container.find_all("li", recursive=False):
        name_el = li.find("span", class_="name")
        if not name_el:
            continue
        label = name_el.get_text(strip=True)
        numbers = [n.get_text(strip=True) for n in li.find_all("span", class_="number")]
        values = [_clean_number(n) for n in numbers]
        values = [v for v in values if v is not None]
        if label == "High / Low" and len(values) == 2:
            ratios["52w_high"], ratios["52w_low"] = values[0], values[1]
        elif values:
            ratios[label] = values[0]

    return ratios


def _parse_time_series_table(html: str, section_id: str, row_map: Dict[str, str]) -> List[Dict]:
    """Parse a Screener.in results table (quarters/profit-loss/balance-sheet/cash-flow)
    into rows of {line_item_key, line_item_label, period_key, value}.

    period_key is the column's data-date-key: an ISO date for a real period-end, or the
    literal string 'TTM' for the trailing-twelve-months column that profit-loss has.
    """
    soup = BeautifulSoup(html, "lxml")
    section = soup.find(id=section_id)
    if not section:
        return []

    table = section.find("table")
    if not table:
        return []

    header_row = table.find("thead").find("tr")
    period_keys = [th.get("data-date-key") for th in header_row.find_all("th")[1:]]

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue
        label = cells[0].get_text(strip=True).rstrip("+").strip()
        if label not in row_map:
            continue
        line_item_key = row_map[label]

        for period_key, td in zip(period_keys, cells[1:]):
            if not period_key:
                continue
            value = _clean_number(td.get_text(strip=True))
            if value is None:
                continue
            rows.append({
                "line_item_key": line_item_key,
                "line_item_label": label,
                "period_key": period_key,
                "value": value,
            })

    return rows


def parse_quarterly_pl(html: str) -> List[Dict]:
    return _parse_time_series_table(html, "quarters", _QUARTERS_ROW_MAP)


def parse_annual_pl(html: str) -> List[Dict]:
    return _parse_time_series_table(html, "profit-loss", _PROFIT_LOSS_ROW_MAP)


def parse_balance_sheet(html: str) -> List[Dict]:
    return _parse_time_series_table(html, "balance-sheet", _BALANCE_SHEET_ROW_MAP)


def parse_cash_flow(html: str) -> List[Dict]:
    """Annual only — India companies don't disclose a quarterly cash flow statement."""
    return _parse_time_series_table(html, "cash-flow", _CASH_FLOW_ROW_MAP)


def parse_shareholding(html: str, period_type: str = "quarterly") -> List[Dict]:
    """Parse #quarterly-shp or #yearly-shp into rows of
    {period_label, period_end_date, promoter_pct, fii_pct, dii_pct, others_pct, num_shareholders}.

    'Others' is everything Screener.in reports beyond Promoters/FIIs/DIIs (typically
    Government + Public), summed, so this stays correct even if a company has an
    unusual extra category.
    """
    soup = BeautifulSoup(html, "lxml")
    container_id = "quarterly-shp" if period_type == "quarterly" else "yearly-shp"
    container = soup.find(id=container_id)
    if not container:
        return []

    table = container.find("table")
    if not table:
        return []

    header_cells = table.find("thead").find("tr").find_all("th")[1:]
    period_labels = [th.get_text(strip=True) for th in header_cells]

    by_period = {label: {"promoter_pct": None, "fii_pct": None, "dii_pct": None,
                          "others_pct": 0.0, "num_shareholders": None} for label in period_labels}
    has_others_data = {label: False for label in period_labels}

    for tr in table.find("tbody").find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue
        label = cells[0].get_text(strip=True).rstrip("+").strip()
        values = [_clean_number(td.get_text(strip=True)) for td in cells[1:]]

        if label == "No. of Shareholders":
            for period_label, value in zip(period_labels, values):
                if value is not None:
                    by_period[period_label]["num_shareholders"] = int(value)
            continue

        key = _SHAREHOLDING_ROW_MAP.get(label)
        for period_label, value in zip(period_labels, values):
            if value is None:
                continue
            if key:
                by_period[period_label][key] = value
            else:
                by_period[period_label]["others_pct"] += value
                has_others_data[period_label] = True

    rows = []
    for period_label in period_labels:
        period_end_date = _parse_period_label_to_date(period_label)
        if not period_end_date:
            continue
        row = {"period_label": period_label, "period_end_date": period_end_date}
        row.update(by_period[period_label])
        if not has_others_data[period_label]:
            row["others_pct"] = None
        rows.append(row)

    return rows


def _parse_period_label_to_date(label: str) -> Optional[str]:
    """'Sep 2025' -> last calendar day of that month, as an ISO date string."""
    m = re.match(r"^([A-Za-z]{3})\s+(\d{4})$", label.strip())
    if not m:
        return None
    month_abbr, year = m.group(1), int(m.group(2))
    month_num = _MONTH_NUM.get(month_abbr)
    if not month_num:
        return None

    days_in_month = {"01": 31, "02": 28, "03": 31, "04": 30, "05": 31, "06": 30,
                      "07": 31, "08": 31, "09": 30, "10": 31, "11": 30, "12": 31}
    # Good enough for display/sorting; leap-year Feb off-by-one doesn't matter here.
    return f"{year}-{month_num}-{days_in_month[month_num]:02d}"


def refresh_company_fundamentals(con, ticker: str, screener_symbol: Optional[str] = None) -> Dict:
    """Fetch and store one company's full fundamentals from Screener.in: top ratios,
    quarterly + annual P&L, balance sheet, cash flow, and shareholding pattern
    (quarterly + yearly).

    Args:
        con: Database connection
        ticker: Our internal ticker (e.g. 'RELIANCE.NS')
        screener_symbol: Override for Screener.in's URL slug if it differs from the
            ticker's base symbol (rare — most NSE symbols match directly)

    Returns:
        {"success": bool, "line_items": int, "shareholding_periods": int, "error": str|None}
    """
    symbol = screener_symbol or ticker.split(".")[0]
    fetched_at = datetime.now(timezone.utc).isoformat()

    try:
        html = fetch_company_page(symbol, consolidated=True)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            try:
                html = fetch_company_page(symbol, consolidated=False)
            except Exception as e2:
                return {"success": False, "line_items": 0, "shareholding_periods": 0, "error": str(e2)}
        else:
            return {"success": False, "line_items": 0, "shareholding_periods": 0, "error": str(e)}
    except Exception as e:
        return {"success": False, "line_items": 0, "shareholding_periods": 0, "error": str(e)}

    cursor = con.cursor()
    line_item_count = 0

    try:
        # --- Quarterly + Annual P&L, Balance Sheet, Cash Flow -> `fundamentals` ---
        quarterly_rows = parse_quarterly_pl(html)
        annual_pl_rows = parse_annual_pl(html)
        balance_sheet_rows = parse_balance_sheet(html)
        cash_flow_rows = parse_cash_flow(html)

        for row in quarterly_rows:
            fiscal_period = _india_fiscal_period_label(row["period_key"])
            _upsert_fundamental(cursor, ticker, fiscal_period, row["period_key"],
                                row["line_item_key"], row["line_item_label"], row["value"], fetched_at)
            line_item_count += 1

        for row in annual_pl_rows + balance_sheet_rows + cash_flow_rows:
            period_key = row["period_key"]
            # India FY is named after its ending year (period ending Mar 2025 = FY2025),
            # matching _india_fiscal_period_label's convention for quarters (Q4FY25).
            fiscal_period = "TTM" if period_key == "TTM" else f"FY{int(period_key[:4])}"
            period_end_date = None if period_key == "TTM" else period_key
            _upsert_fundamental(cursor, ticker, fiscal_period, period_end_date,
                                row["line_item_key"], row["line_item_label"], row["value"], fetched_at)
            line_item_count += 1

        # --- Top ratios (current point-in-time) -> `fundamentals_latest` ---
        ratios = parse_top_ratios(html)
        _upsert_fundamentals_latest(cursor, ticker, ratios, annual_pl_rows, balance_sheet_rows, fetched_at)

        # --- Shareholding pattern (quarterly + yearly) -> `shareholding_pattern` ---
        shareholding_rows = parse_shareholding(html, "quarterly") + parse_shareholding(html, "yearly")
        seen_dates = set()
        shareholding_count = 0
        for row in shareholding_rows:
            if row["period_end_date"] in seen_dates:
                continue
            seen_dates.add(row["period_end_date"])
            cursor.execute("""
                INSERT OR REPLACE INTO shareholding_pattern
                (ticker, period_end_date, period_label, promoter_pct, fii_pct, dii_pct, others_pct,
                 num_shareholders, source, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ticker, row["period_end_date"], row["period_label"], row["promoter_pct"],
                  row["fii_pct"], row["dii_pct"], row["others_pct"], row["num_shareholders"],
                  "SCREENER_IN", fetched_at))
            shareholding_count += 1

        con.commit()
    except Exception as e:
        con.rollback()
        return {"success": False, "line_items": 0, "shareholding_periods": 0,
                "error": f"{type(e).__name__}: {e}"}

    return {"success": True, "line_items": line_item_count,
            "shareholding_periods": shareholding_count, "error": None}


def _upsert_fundamental(cursor, ticker, fiscal_period, period_end_date, line_item_key,
                        line_item_label, value, fetched_at):
    cursor.execute("""
        INSERT OR REPLACE INTO fundamentals
        (ticker, fiscal_period, period_end_date, line_item_key, line_item_label,
         value, unit, source, is_custom, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ticker, fiscal_period, period_end_date, line_item_key, line_item_label,
          value, "INR_CR", "SCREENER_IN", 0, fetched_at))


def _upsert_fundamentals_latest(cursor, ticker, ratios, annual_pl_rows, balance_sheet_rows, fetched_at):
    """Combine #top-ratios with a couple of balance-sheet-derived figures (Debt/Equity,
    PEG needs YoY EPS which the caller doesn't have here, so PEG is computed in the UI
    layer from stored history instead of duplicated here)."""
    market_cap = ratios.get("Market Cap")
    current_price = ratios.get("Current Price")
    pe_ratio = ratios.get("Stock P/E")
    book_value = ratios.get("Book Value")
    dividend_yield = ratios.get("Dividend Yield")
    roce = ratios.get("ROCE")
    roe = ratios.get("ROE")
    face_value = ratios.get("Face Value")
    high_52w = ratios.get("52w_high")
    low_52w = ratios.get("52w_low")

    debt = next((r["value"] for r in balance_sheet_rows if r["line_item_key"] == "debt"
                 and r["period_key"] != "TTM"), None)
    latest_year_key = max((r["period_key"] for r in balance_sheet_rows if r["period_key"] != "TTM"),
                          default=None)
    equity_capital = next((r["value"] for r in balance_sheet_rows if r["line_item_key"] == "equity_capital"
                           and r["period_key"] == latest_year_key), None)
    reserves = next((r["value"] for r in balance_sheet_rows if r["line_item_key"] == "reserves"
                     and r["period_key"] == latest_year_key), None)
    net_worth = (equity_capital + reserves) if equity_capital is not None and reserves is not None else None
    debt_to_equity = (debt / net_worth) if debt is not None and net_worth else None
    pb_ratio = (current_price / book_value) if current_price is not None and book_value else None

    cursor.execute("""
        INSERT OR REPLACE INTO fundamentals_latest
        (ticker, fiscal_period, pe_ratio, forward_pe, pb_ratio, debt_to_equity, roe,
         profit_margin, revenue_growth, earnings_growth, dividend_yield, market_cap,
         current_price, high_52w, low_52w, book_value, roce, face_value, debt, net_worth,
         source, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ticker, "LATEST", pe_ratio, None, pb_ratio, debt_to_equity, roe,
          None, None, None, dividend_yield, market_cap,
          current_price, high_52w, low_52w, book_value, roce, face_value, debt, net_worth,
          "SCREENER_IN", fetched_at))


def refresh_india_fundamentals(con, tickers: List[str], progress_callback=None,
                              delay_seconds: float = SCREENER_IN_REQUEST_DELAY_SECONDS) -> Dict:
    """Bulk refresh: fetch + store fundamentals for each ticker, with a delay between
    requests to stay respectful of Screener.in's servers."""
    total = len(tickers)
    succeeded, failed, failed_list = 0, 0, []

    for idx, ticker in enumerate(tickers):
        if progress_callback:
            progress_callback(idx + 1, total, f"Fetching {ticker}...")

        result = refresh_company_fundamentals(con, ticker)
        if result["success"]:
            succeeded += 1
        else:
            failed += 1
            failed_list.append(ticker)
            logger.warning(f"Failed to refresh {ticker}: {result['error']}")

        if idx < total - 1:
            time.sleep(delay_seconds)

    return {"attempted": total, "succeeded": succeeded, "failed": failed, "failed_tickers": failed_list}
