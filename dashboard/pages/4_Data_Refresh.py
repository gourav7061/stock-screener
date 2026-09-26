"""Data Refresh page — trigger pipelines with progress."""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stockscreener.db import get_connection, get_last_refresh
from stockscreener.config import DB_PATH

st.set_page_config(page_title="Data Refresh", layout="wide")
st.title("🔄 Data Refresh & Admin")
st.markdown("Manually trigger data pipelines to update cache.")

con = get_connection(DB_PATH)

st.warning("⚠️ **Beta Feature**: Data pipelines are under development. In v1, use command-line tools:")
st.code("""
# Build universe (US + India tickers)
python tools/build_universe.py --market ALL

# Refresh US fundamentals from SEC EDGAR
python tools/refresh_us_fundamentals.py --tickers AAPL MSFT

# Refresh price data and technicals
python tools/refresh_prices.py --market US --period 2y
""", language="bash")

st.subheader("Refresh Status")

# Show last refresh times
try:
    cursor = con.cursor()
    cursor.execute("""
        SELECT data_type, market, status, finished_at, tickers_succeeded, tickers_failed
        FROM data_refresh_log
        ORDER BY finished_at DESC
        LIMIT 10
    """)

    logs = cursor.fetchall()
    if logs:
        for log in logs:
            data_type, market, status, finished_at, succeeded, failed = log
            status_icon = "✓" if status == "success" else "⚠️" if status == "partial" else "✗"

            col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
            with col1:
                st.write(f"{status_icon} {data_type} ({market or 'N/A'})")
            with col2:
                st.write(f"{status}")
            with col3:
                if succeeded or failed:
                    st.write(f"{succeeded}/{succeeded + failed}")
            with col4:
                if finished_at:
                    st.write(f"{finished_at[:10]}")
    else:
        st.info("📦 No refresh history yet. Click the buttons below to load data.")
except Exception as e:
    st.info("📦 No refresh history yet. Click the buttons below to start loading stock data.")

st.subheader("India Fundamentals Note")
st.info("""
🇮🇳 **Tiered Coverage**: Indian fundamentals are populated only for Nifty 500 + BSE 500 stocks (~700-900 names).
The full India universe (~5000+ stocks) has technicals only (price/volume data via yfinance).

This is by design for v1 — free comprehensive Indian fundamentals are not reliably available.
Upgrade to a paid data API to expand coverage.
""")

con.close()
