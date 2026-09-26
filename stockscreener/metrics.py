"""Metrics registry — built-in and user-custom line items."""

import sqlite3
from typing import Dict, List


BUILT_IN_METRICS = {
    # Technical (price / chart based)
    "price": {"label": "Current Price", "category": "Technical", "unit": ""},
    "sma20": {"label": "20-Day Average Price (SMA20)", "category": "Technical", "unit": ""},
    "sma50": {"label": "50-Day Average Price (SMA50)", "category": "Technical", "unit": ""},
    "sma150": {"label": "150-Day Average Price (SMA150)", "category": "Technical", "unit": ""},
    "sma200": {"label": "200-Day Average Price (SMA200)", "category": "Technical", "unit": ""},
    "sma220": {"label": "220-Day Average Price (SMA220)", "category": "Technical", "unit": ""},
    "ema220": {"label": "220-Day Exponential Average (EMA220)", "category": "Technical", "unit": ""},
    "rsi14": {"label": "RSI (14-day momentum score)", "category": "Technical", "unit": ""},
    "pct_change_1d": {"label": "% Change - 1 Day", "category": "Technical", "unit": "%"},
    "pct_change_1m": {"label": "% Change - 1 Month", "category": "Technical", "unit": "%"},
    "pct_change_3m": {"label": "% Change - 3 Months", "category": "Technical", "unit": "%"},
    "pct_change_1y": {"label": "% Change - 1 Year", "category": "Technical", "unit": "%"},
    "pct_from_52w_high": {"label": "% Below 52-Week High", "category": "Technical", "unit": "%"},
    "pct_from_52w_low": {"label": "% Above 52-Week Low", "category": "Technical", "unit": "%"},
    "52w_low": {"label": "52-Week Low", "category": "Technical", "unit": ""},
    "52w_low_25pct": {"label": "52-Week Low + 25%", "category": "Technical", "unit": ""},
    "volume": {"label": "Latest Volume", "category": "Technical", "unit": ""},
    "avg_volume_20d": {"label": "20-Day Average Volume", "category": "Technical", "unit": ""},
    "macd": {"label": "MACD (Moving Average Convergence Divergence)", "category": "Technical", "unit": ""},
    "macd_signal": {"label": "MACD Signal Line", "category": "Technical", "unit": ""},
    "macd_hist": {"label": "MACD Histogram", "category": "Technical", "unit": ""},
    "bb_upper": {"label": "Bollinger Bands Upper", "category": "Technical", "unit": ""},
    "bb_lower": {"label": "Bollinger Bands Lower", "category": "Technical", "unit": ""},
    "bb_mid": {"label": "Bollinger Bands Middle (SMA)", "category": "Technical", "unit": ""},
    "bb_percent_b": {"label": "Bollinger Bands %B", "category": "Technical", "unit": "%"},
    "volume_spike_ratio": {"label": "Volume Spike Ratio (vs 20d avg)", "category": "Technical", "unit": ""},

    # Fundamental (company financial health)
    "pe_ratio": {"label": "P/E Ratio", "category": "Fundamental", "unit": ""},
    "forward_pe": {"label": "Forward P/E Ratio", "category": "Fundamental", "unit": ""},
    "pb_ratio": {"label": "P/B Ratio (Price to Book)", "category": "Fundamental", "unit": ""},
    "debt_to_equity": {"label": "Debt to Equity", "category": "Fundamental", "unit": ""},
    "roe": {"label": "Return on Equity (ROE)", "category": "Fundamental", "unit": "%"},
    "profit_margin": {"label": "Profit Margin", "category": "Fundamental", "unit": "%"},
    "revenue_growth": {"label": "Revenue Growth (YoY)", "category": "Fundamental", "unit": "%"},
    "earnings_growth": {"label": "Earnings Growth (YoY)", "category": "Fundamental", "unit": "%"},
    "dividend_yield": {"label": "Dividend Yield", "category": "Fundamental", "unit": "%"},
    "market_cap": {"label": "Market Cap", "category": "Fundamental", "unit": ""},
}

OPERATORS = {
    ">": "is greater than",
    "<": "is less than",
    ">=": "is greater than or equal to",
    "<=": "is less than or equal to",
    "==": "is equal to",
    "!=": "is not equal to",
}


def get_metrics_registry(con: sqlite3.Connection = None) -> Dict[str, Dict]:
    """Get the combined registry of built-in + custom line items.

    Args:
        con: Database connection (optional). If provided, custom line items are fetched.

    Returns:
        Dictionary of metric_key -> {label, category, unit}
    """
    registry = BUILT_IN_METRICS.copy()

    if con:
        try:
            cursor = con.cursor()
            cursor.execute("SELECT line_item_key, label, category, unit FROM custom_line_items")
            for row in cursor.fetchall():
                registry[row[0]] = {
                    "label": row[1],
                    "category": row[2],
                    "unit": row[3] or "",
                }
        except Exception:
            # custom_line_items table doesn't exist yet, skip custom metrics
            pass

    return registry


def get_metric_label(metric_key: str, con: sqlite3.Connection = None) -> str:
    """Get the friendly label for a metric."""
    registry = get_metrics_registry(con)
    return registry.get(metric_key, {}).get("label", metric_key)


def is_fundamental_metric(metric_key: str, con: sqlite3.Connection = None) -> bool:
    """Check if a metric is a fundamental (as opposed to technical)."""
    registry = get_metrics_registry(con)
    return registry.get(metric_key, {}).get("category") == "Fundamental"
