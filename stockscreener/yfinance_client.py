"""Throttled yfinance wrapper with retry logic."""

import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timezone
import time
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_prices_batch(tickers: List[str], period: str = "2y", start: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """Fetch OHLCV price data for a batch of tickers with retry logic.

    Args:
        tickers: List of tickers (e.g., ['AAPL', 'MSFT', 'RELIANCE.NS'])
        period: Period string (e.g., '1y', '2y', '5y')
        start: Start date (overrides period if set)

    Returns:
        Dict mapping ticker to DataFrame with OHLCV columns
    """
    if not tickers:
        return {}

    try:
        # yfinance.download returns a single DataFrame if one ticker, or dict if multiple
        data = yf.download(tickers, period=period, start=start, group_by="ticker", threads=True, progress=False)

        if len(tickers) == 1:
            # Single ticker: convert to dict
            return {tickers[0]: data}
        else:
            # Multiple tickers: convert to dict of DataFrames
            return {ticker: data[ticker] if ticker in data.columns else data[ticker]
                   for ticker in tickers if ticker in data}

    except Exception as e:
        logger.error(f"yfinance batch fetch failed: {e}")
        raise


def get_last_stored_date(con, ticker: str) -> Optional[str]:
    """Get the most recent price date stored for a ticker.

    Returns ISO date string (YYYY-MM-DD) or None if no data.
    """
    cursor = con.cursor()
    cursor.execute("SELECT MAX(date) FROM prices WHERE ticker = ?", (ticker,))
    row = cursor.fetchone()
    return row[0] if row[0] else None
