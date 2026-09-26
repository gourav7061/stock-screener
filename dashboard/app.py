"""Main Streamlit app — stock screener dashboard."""

import streamlit as st
from datetime import datetime, timezone
import sqlite3
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stockscreener.db import init_db, get_connection
from stockscreener.config import DB_PATH, STALENESS_WARNING_DAYS
from stockscreener.metrics import get_metrics_registry

# Initialize DB
try:
    init_db(DB_PATH)
except:
    pass

st.set_page_config(
    page_title="Stock Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Professional Stock Screener")
st.markdown("Build strategies. Screen stocks. Analyze fundamentals.")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio("", [
        "📊 Dashboard",
        "🛠️ Strategy Builder",
        "🔍 Run Screener",
        "📋 Fundamentals",
        "🔄 Data Refresh"
    ])

# Main content
if page == "📊 Dashboard":
    st.subheader("Overview")

    try:
        con = get_connection(DB_PATH)
        cursor = con.cursor()

        # Row counts
        try:
            cursor.execute("SELECT COUNT(*) FROM companies WHERE market = 'US'")
            us_count = cursor.fetchone()[0]
        except:
            us_count = 0

        try:
            cursor.execute("SELECT COUNT(*) FROM companies WHERE market = 'IN'")
            in_count = cursor.fetchone()[0]
        except:
            in_count = 0

        try:
            cursor.execute("SELECT COUNT(*) FROM technicals_latest")
            tech_count = cursor.fetchone()[0]
        except:
            tech_count = 0

        try:
            cursor.execute("SELECT COUNT(*) FROM strategies")
            strat_count = cursor.fetchone()[0]
        except:
            strat_count = 0

        # Last refresh times
        try:
            cursor.execute("""
                SELECT data_type, market, MAX(finished_at) as last_refresh
                FROM data_refresh_log
                WHERE status = 'success'
                GROUP BY data_type, market
                ORDER BY last_refresh DESC
            """)
            refreshes = {f"{row[0]}_{row[1] or 'N/A'}": row[2] for row in cursor.fetchall()}
        except:
            refreshes = {}

        con.close()

        # KPI tiles
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("US Stocks", us_count)
        with col2:
            st.metric("India Stocks", in_count)
        with col3:
            st.metric("With Technicals", tech_count)
        with col4:
            st.metric("Saved Strategies", strat_count)

        # Data refresh status
        st.subheader("Data Refresh Status")
        if refreshes:
            for key, ts in refreshes.items():
                if ts:
                    dt = datetime.fromisoformat(ts)
                    ago_mins = (datetime.now(timezone.utc).replace(tzinfo=None) - dt.replace(tzinfo=None)).total_seconds() / 60
                    st.write(f"✓ {key}: {ago_mins:.0f} minutes ago")
                else:
                    st.write(f"⚠️ {key}: Not refreshed yet")
        else:
            st.info("📦 No data loaded yet. Go to **Data Refresh** page to load stock data.")

    except Exception as e:
        st.error(f"Database error: {str(e)}")
        st.info("📦 Go to **Data Refresh** page to initialize and load data.")

elif page == "🛠️ Strategy Builder":
    st.subheader("Strategy Builder")
    # Delegated to pages/1_Strategy_Builder.py
    st.write("See sidebar → Strategy Builder page")

elif page == "🔍 Run Screener":
    st.subheader("Run Screener")
    # Delegated to pages/2_Run_Screener.py
    st.write("See sidebar → Run Screener page")

elif page == "📋 Fundamentals":
    st.subheader("Fundamentals Analysis")
    # Delegated to pages/3_Fundamentals.py
    st.write("See sidebar → Fundamentals page")

elif page == "🔄 Data Refresh":
    st.subheader("Data Refresh & Admin")
    # Delegated to pages/4_Data_Refresh.py
    st.write("See sidebar → Data Refresh page")
