"""Fundamentals page — view 10-year financial line items."""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stockscreener.db import get_connection
from stockscreener.config import DB_PATH

st.set_page_config(page_title="Fundamentals", layout="wide")
st.title("📋 Fundamentals Analysis")
st.markdown("View up to 10 years of financial line items per stock.")

con = get_connection(DB_PATH)
cursor = con.cursor()

# Step 1: Pick ticker
st.subheader("1. Search Stock")

cursor.execute("SELECT DISTINCT ticker, name FROM companies WHERE is_active = 1 ORDER BY ticker")
all_tickers = {f"{row[0]} ({row[1]})": row[0] for row in cursor.fetchall()}

if not all_tickers:
    st.info("No stocks in database yet")
    con.close()
    st.stop()

ticker_display = st.selectbox("Stock", list(all_tickers.keys()))
ticker = all_tickers[ticker_display]

# Get stock info
cursor.execute("SELECT market, name, has_fundamentals FROM companies WHERE ticker = ?", (ticker,))
stock_info = cursor.fetchone()
if not stock_info:
    st.error("Stock not found")
    con.close()
    st.stop()

market, name, has_fundamentals = stock_info

# Step 2: View fundamentals
st.subheader("2. Financial Data")

if not has_fundamentals:
    st.warning(f"⚠️ Fundamentals not available for {ticker} (outside coverage tier)")
    if market == "IN":
        st.info("🇮🇳 Indian fundamentals are only available for Nifty 500 + BSE 500 stocks in v1.")
else:
    # Fetch fundamentals
    cursor.execute("""
        SELECT fiscal_period, period_end_date, line_item_key, line_item_label, value, unit, source
        FROM fundamentals
        WHERE ticker = ?
        ORDER BY period_end_date DESC
    """, (ticker,))

    rows = cursor.fetchall()

    if not rows:
        st.info(f"No fundamentals data for {ticker} yet. Run 'Data Refresh' to populate.")
    else:
        # Group by line item
        line_items = {}
        for period, date, key, label, value, unit, source in rows:
            if key not in line_items:
                line_items[key] = {"label": label, "unit": unit, "data": []}
            line_items[key]["data"].append((period, date, value, source))

        # Display line items
        st.markdown(f"**{ticker}** — {name}")

        for key, info in sorted(line_items.items(), key=lambda x: x[0]):
            with st.expander(f"{info['label']} ({info['unit'] or 'N/A'})"):
                df_data = []
                for period, date, value, source in sorted(info["data"], key=lambda x: x[1], reverse=True)[:10]:
                    df_data.append({
                        "Period": period,
                        "End Date": date,
                        "Value": value,
                        "Source": source
                    })

                if df_data:
                    st.dataframe(pd.DataFrame(df_data), use_container_width=True)
                else:
                    st.write("No data")

# Step 3: Add custom line item (future)
st.subheader("3. Custom Line Items (Coming Soon)")
st.info("In v2, you'll be able to add custom line items from company filings to track alongside standard metrics.")

con.close()
