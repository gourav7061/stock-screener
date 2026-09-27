"""Fetch and parse US fundamentals from SEC EDGAR XBRL data."""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# SEC XBRL tag mappings to standard line items
US_GAAP_MAP = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomer", "SalesRevenueNet", "NetRevenue"],
    "net_income": ["NetIncomeLoss", "NetIncome"],
    "operating_income": ["OperatingIncome", "IncomeFromContinuingOperationsBeforeTax"],
    "total_assets": ["Assets"],
    "total_liabilities": ["Liabilities"],
    "stockholders_equity": ["StockholdersEquity", "CommonStockholdersEquity"],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "free_cash_flow": ["FreeCashFlow"],
    "eps_diluted": ["EarningsPerShareDiluted", "BasicEarningsPerShare"],
    "long_term_debt": ["LongTermDebt", "LongTermDebtNoncurrent"],
    "current_assets": ["AssetsCurrent"],
    "current_liabilities": ["LiabilitiesCurrent"],
    "shares_outstanding": ["EntityCommonStockSharesOutstanding", "WeightedAverageNumberOfDilutedSharesAdjustment"],
}

def fetch_companyfacts(cik: str, user_agent: str) -> Dict:
    """Fetch company facts (all XBRL data) for a single CIK.

    Args:
        cik: 10-digit zero-padded CIK
        user_agent: Required by SEC (must include email)

    Returns:
        Company facts JSON dict or empty dict on error
    """
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    headers = {"User-Agent": user_agent}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.debug(f"Failed to fetch companyfacts for CIK {cik}: {e}")
        return {}


def normalize_companyfacts(cik: str, ticker: str, facts_json: Dict, line_item_map: Dict) -> List[Dict]:
    """Normalize SEC XBRL facts into standardized rows.

    Args:
        cik: CIK for reference
        ticker: Stock ticker
        facts_json: Raw companyfacts JSON from SEC
        line_item_map: Mapping of standard keys to XBRL tags

    Returns:
        List of dicts ready for insertion into fundamentals table
    """
    rows = []

    if not facts_json or "facts" not in facts_json:
        return rows

    facts = facts_json.get("facts", {})
    us_gaap = facts.get("us-gaap", {})

    for line_item_key, xbrl_tags in line_item_map.items():
        for xbrl_tag in xbrl_tags:
            if xbrl_tag not in us_gaap:
                continue

            tag_data = us_gaap[xbrl_tag]
            units = tag_data.get("units", {})

            # Prefer USD, fallback to other units
            values = units.get("USD", []) or next(iter(units.values()), [])

            for entry in values:
                if entry.get("val") is None:
                    continue

                # Extract fiscal period from filing date
                filing_date = entry.get("filed", "")
                end_date = entry.get("end", "")

                if not end_date:
                    continue

                # Determine fiscal period
                year = int(end_date[:4])
                fiscal_period = f"FY{year}"

                rows.append({
                    "ticker": ticker,
                    "fiscal_period": fiscal_period,
                    "period_end_date": end_date,
                    "line_item_key": line_item_key,
                    "line_item_label": xbrl_tag,
                    "value": entry.get("val"),
                    "unit": "USD",
                    "source": "SEC_EDGAR",
                    "is_custom": 0,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                })

    # Deduplicate: keep most recent filing for each (ticker, fiscal_period, line_item_key)
    seen = {}
    for row in reversed(sorted(rows, key=lambda x: x["period_end_date"])):
        key = (row["ticker"], row["fiscal_period"], row["line_item_key"])
        if key not in seen:
            seen[key] = row

    return list(seen.values())
