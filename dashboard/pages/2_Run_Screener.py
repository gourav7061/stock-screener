"""Run Screener page — execute strategies against cached data."""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stockscreener.db import get_connection, get_last_refresh
from stockscreener.config import DB_PATH, STALENESS_WARNING_DAYS
from stockscreener.strategy_engine import list_strategies, load_strategy, run_strategy_against_db
from stockscreener.metrics import get_metrics_registry

st.set_page_config(page_title="Run Screener", layout="wide")
st.title("🔍 Run Screener")
st.markdown("Execute your strategy against cached stock data.")

con = get_connection(DB_PATH)
metrics_registry = get_metrics_registry(con)

# Check data freshness
last_tech = get_last_refresh(con, "prices", market="US")
if last_tech:
    dt = datetime.fromisoformat(last_tech["finished_at"])
    ago_days = (datetime.now(timezone.utc).replace(tzinfo=None) - dt.replace(tzinfo=None)).days
    if ago_days > STALENESS_WARNING_DAYS:
        st.warning(f"⚠️ Price data is {ago_days} days old. Go to 'Data Refresh' to update.")

# Step 1: Pick strategy
st.subheader("1. Choose Strategy")
strategies = list_strategies(con)

if not strategies:
    st.info("No strategies saved yet. Go to 'Strategy Builder' to create one.")
    con.close()
    st.stop()

strategy_names = [s["name"] for s in strategies]
chosen_name = st.selectbox("Strategy", strategy_names)

# Load strategy
chosen = next((s for s in strategies if s["name"] == chosen_name), None)
strategy = load_strategy(con, chosen["id"])

st.markdown(f"**Rules**: {strategy.get('name')}")

# Step 2: Pick market/universe
st.subheader("2. Choose Universe")

market = st.radio("Market", ["US", "India", "Both"])
universe_choice = st.radio("Scope", ["Full Universe", "Index Only", "Custom List"])

if universe_choice == "Custom List":
    custom_tickers = st.text_area("Ticker symbols (comma or line separated)", placeholder="AAPL, MSFT, RELIANCE.NS")
    tickers = [t.strip().upper() for t in custom_tickers.replace("\n", ",").split(",") if t.strip()]
else:
    # Fetch from DB
    cursor = con.cursor()
    if market == "US":
        if universe_choice == "Index Only":
            cursor.execute("SELECT ticker FROM companies WHERE market = 'US' LIMIT 10")
        else:
            cursor.execute("SELECT ticker FROM companies WHERE market = 'US'")
    elif market == "India":
        if universe_choice == "Index Only":
            cursor.execute("SELECT ticker FROM companies WHERE market = 'IN' AND index_membership IS NOT NULL LIMIT 50")
        else:
            cursor.execute("SELECT ticker FROM companies WHERE market = 'IN'")
    else:  # Both
        cursor.execute("SELECT ticker FROM companies")

    tickers = [row[0] for row in cursor.fetchall()]

st.markdown(f"**Universe**: {len(tickers)} stocks")

# Step 3: Run
st.subheader("3. Screen")

if st.button("▶️ Run Screener", type="primary"):
    if not tickers:
        st.error("No tickers to screen")
    else:
        with st.spinner(f"Screening {len(tickers)} stocks..."):
            result_df = run_strategy_against_db(con, strategy, tickers, metrics_registry)

        if result_df.empty:
            st.warning("❌ No stocks matched this strategy")
        else:
            st.success(f"✅ {len(result_df)} stock(s) matched out of {len(tickers)} screened")

            # Display results
            st.subheader("Results")
            st.dataframe(result_df, use_container_width=True)

            # CSV export
            csv = result_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download as CSV",
                csv,
                f"{strategy['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv"
            )

con.close()
