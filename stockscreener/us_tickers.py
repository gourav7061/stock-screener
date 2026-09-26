"""Fetch US ticker universe from SEC and Nasdaq sources."""

import pandas as pd
import requests
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# S&P 100 — largest 100 US companies (for initial testing, hardcoded)
SP100_DATA = [
    ("AAPL", "NASDAQ", "Apple Inc.", "0000320193"),
    ("MSFT", "NASDAQ", "Microsoft Corporation", "0000789019"),
    ("GOOGL", "NASDAQ", "Alphabet Inc.", "0001018724"),
    ("AMZN", "NASDAQ", "Amazon.com, Inc.", "0001018724"),
    ("NVDA", "NASDAQ", "NVIDIA Corporation", "0001045810"),
    ("META", "NASDAQ", "Meta Platforms, Inc.", "0001326801"),
    ("TSLA", "NASDAQ", "Tesla, Inc.", "0001652044"),
    ("BRK-B", "NYSE", "Berkshire Hathaway Inc.", "0001067983"),
    ("JPM", "NYSE", "JPMorgan Chase & Co.", "0000019617"),
    ("V", "NYSE", "Visa Inc.", "0001403161"),
    ("UNH", "NYSE", "UnitedHealth Group Incorporated", "0000731766"),
    ("XOM", "NYSE", "Exxon Mobil Corporation", "0000034088"),
    ("JNJ", "NYSE", "Johnson & Johnson", "0000200406"),
    ("WMT", "NYSE", "Walmart Inc.", "0000104169"),
    ("MA", "NYSE", "Mastercard Incorporated", "0001141391"),
    ("PG", "NYSE", "The Procter & Gamble Company", "0000080424"),
    ("HD", "NYSE", "The Home Depot, Inc.", "0000354950"),
    ("CVX", "NYSE", "Chevron Corporation", "0000093410"),
    ("MRK", "NYSE", "Merck & Co., Inc.", "0000059364"),
    ("ABBV", "NYSE", "AbbVie Inc.", "0001551152"),
    ("COST", "NASDAQ", "Costco Wholesale Corporation", "0000909832"),
    ("PEP", "NASDAQ", "PepsiCo, Inc.", "0000076304"),
    ("KO", "NYSE", "The Coca-Cola Company", "0000021344"),
    ("AVGO", "NASDAQ", "Broadcom Inc.", "0001347925"),
    ("ADBE", "NASDAQ", "Adobe Inc.", "0000796343"),
    ("CRM", "NYSE", "Salesforce, Inc.", "0001108772"),
    ("NFLX", "NASDAQ", "Netflix, Inc.", "0001065280"),
    ("AMD", "NASDAQ", "Advanced Micro Devices, Inc.", "0000002488"),
    ("INTC", "NASDAQ", "Intel Corporation", "0000050104"),
    ("DIS", "NYSE", "The Walt Disney Company", "0000018732"),
    ("CSCO", "NASDAQ", "Cisco Systems, Inc.", "0000858877"),
    ("VZ", "NYSE", "Verizon Communications Inc.", "0000732712"),
    ("IBM", "NYSE", "International Business Machines", "0000051143"),
    ("MU", "NASDAQ", "Micron Technology, Inc.", "0000723125"),
    ("QCOM", "NASDAQ", "QUALCOMM Incorporated", "0000804842"),
    ("HON", "NASDAQ", "Honeywell International Inc.", "0000773840"),
    ("GE", "NYSE", "General Electric Company", "0000040545"),
    ("CAT", "NYSE", "Caterpillar Inc.", "0000018230"),
    ("BA", "NYSE", "The Boeing Company", "0000012927"),
    ("MMM", "NYSE", "3M Company", "0000066740"),
]


def build_us_universe(test_mode: bool = True) -> pd.DataFrame:
    """Build US ticker universe.

    Args:
        test_mode: If True, return S&P 100 tickers (hardcoded). If False, fetch full universe.

    Returns:
        DataFrame with columns: ticker, exchange, market, name, cik.
    """
    if test_mode:
        # Test mode: hardcoded S&P 100 data
        rows = []
        for ticker, exchange, name, cik in SP100_DATA:
            rows.append({
                "ticker": ticker,
                "exchange": exchange,
                "market": "US",
                "name": name,
                "cik": cik,
            })

        return pd.DataFrame(rows)
    else:
        # Full universe mode (requires API calls)
        logger.warning("Full US universe fetch not yet implemented")
        return pd.DataFrame(columns=["ticker", "exchange", "market", "name", "cik"])
