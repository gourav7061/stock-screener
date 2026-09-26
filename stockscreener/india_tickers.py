"""Fetch India ticker universe from NSE and BSE sources."""

import pandas as pd
import requests
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

# Nifty 50 — top 50 Indian companies (for initial testing)
NIFTY50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "BHARTIARTL.NS",
    "ITC.NS", "LT.NS", "SBIN.NS", "HINDUNILVR.NS", "AXISBANK.NS", "BAJFINANCE.NS",
    "KOTAKBANK.NS", "MARUTI.NS", "SUNPHARMA.NS", "M&M.NS", "TITAN.NS", "ULTRACEMCO.NS",
    "NTPC.NS", "ONGC.NS", "TATAMOTORS.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ASIANPAINT.NS",
    "BAJAJFINSV.NS", "BAJAJ-AUTO.NS", "BEL.NS", "CIPLA.NS", "COALINDIA.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS",
    "INDUSINDBK.NS", "JSWSTEEL.NS", "NESTLEIND.NS", "POWERGRID.NS", "SBILIFE.NS",
    "SHRIRAMFIN.NS", "TATACONSUM.NS", "TATASTEEL.NS", "TECHM.NS", "TRENT.NS", "WIPRO.NS",
    "APOLLOHOSP.NS", "BPCL.NS",
]

# Nifty 500 membership (canonical list) — for determining has_fundamentals in India
NIFTY500_TICKERS = set(NIFTY50_TICKERS + [
    "DIVISLAB.NS", "LTIM.NS", "CANBK.NS", "SIEMENS.NS", "IOCL.NS", "LUPIN.NS",
    "IRCTC.NS", "PIDILITEINDS.NS", "GODREJCP.NS", "DABUR.NS", "MARICO.NS", "ESCORTS.NS",
])


def get_nifty50() -> List[str]:
    """Return Nifty 50 ticker list for testing."""
    return NIFTY50_TICKERS


def get_nse_equity_universe() -> pd.DataFrame:
    """Fetch NSE listed companies.

    Returns a DataFrame with columns: ticker, name, exchange, market.
    NSE is the preferred source; note: adds .NS suffix to tickers per yfinance convention.
    """
    url = "https://www1.nseindia.com/content/equities/EQUITY_L.csv"
    try:
        df = pd.read_csv(url)
        # Typical columns: SYMBOL, NAME, SERIES, etc.
        if "SYMBOL" in df.columns and "NAME" in df.columns:
            df = df[df["SERIES"] == "EQ"]  # Equity series only
            rows = []
            for _, row in df.iterrows():
                rows.append({
                    "ticker": f"{row['SYMBOL']}.NS",
                    "name": row["NAME"],
                    "exchange": "NSE",
                    "market": "IN",
                })
            return pd.DataFrame(rows)
    except Exception as e:
        logger.error(f"Failed to fetch NSE equity list: {e}")

    return pd.DataFrame(columns=["ticker", "name", "exchange", "market"])


def get_bse_equity_universe() -> pd.DataFrame:
    """Fetch BSE listed companies.

    Returns a DataFrame with columns: ticker, name, exchange, market.
    Note: BSE is fallback; NSE is preferred for dual-listed companies.
    """
    # BSE doesn't have an easily accessible free CSV, so we'll use a fallback list
    # In production, you'd fetch from BSE's website or use an API
    logger.warning("BSE universe fetch not implemented — using Nifty 50 + Nifty 500 as proxy")

    return pd.DataFrame(columns=["ticker", "name", "exchange", "market"])


def get_nifty500_membership() -> Set[str]:
    """Return set of Nifty 500 member tickers (with .NS suffix)."""
    return NIFTY500_TICKERS


def get_bse500_membership() -> Set[str]:
    """Return set of BSE 500 member tickers (with .BO suffix).

    For v1, return empty set since BSE data is harder to get free.
    """
    return set()


def build_india_universe(test_mode: bool = True) -> pd.DataFrame:
    """Build India ticker universe.

    Args:
        test_mode: If True, return only Nifty 50. If False, return full universe.

    Returns:
        DataFrame with columns: ticker, exchange, market, name, index_membership.
    """
    if test_mode:
        # Test mode: just Nifty 50
        rows = []
        for ticker in NIFTY50_TICKERS:
            rows.append({
                "ticker": ticker,
                "exchange": "NSE",
                "market": "IN",
                "name": ticker.replace(".NS", ""),  # Placeholder
                "index_membership": "NIFTY50",
            })
        return pd.DataFrame(rows)
    else:
        # Full universe mode
        nse = get_nse_equity_universe()
        bse = get_bse_equity_universe()

        # Combine NSE + BSE
        combined = pd.concat([nse, bse], ignore_index=True)

        # Mark index membership
        nifty500 = get_nifty500_membership()
        bse500 = get_bse500_membership()

        def get_membership(ticker):
            memberships = []
            if ticker in nifty500:
                memberships.append("NIFTY500")
            if ticker in bse500:
                memberships.append("BSE500")
            return ",".join(memberships) if memberships else None

        combined["index_membership"] = combined["ticker"].apply(get_membership)

        return combined[["ticker", "exchange", "market", "name", "index_membership"]]
