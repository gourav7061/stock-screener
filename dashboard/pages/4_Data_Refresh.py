"""Data Refresh page — trigger pipelines with progress."""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stockscreener.db import init_db, get_connection
from stockscreener.config import DB_PATH
from tools.build_universe import populate_companies
from tools.refresh_prices import refresh_prices
from tools.refresh_india_fundamentals import refresh_india_fundamentals

st.set_page_config(page_title="Data Refresh", layout="wide")
st.title("🔄 Data Refresh & Admin")
st.markdown("Load stock data directly from this page — no command line needed.")

try:
    init_db(DB_PATH)
except Exception:
    pass

con = get_connection(DB_PATH)

# ============================================================================
# STEP 1: BUILD COMPANY UNIVERSE
# ============================================================================
st.subheader("1. Build Company Universe")
st.caption("Loads ticker symbols into the `companies` table. Do this first — the screener has nothing to run against until this step completes.")

col1, col2 = st.columns(2)
full_universe = st.checkbox("Load full universe (slower)", value=False,
                            help="Unchecked = small test set (S&P 100 / Nifty 50). Checked = full market (thousands of tickers, much slower).")

with col1:
    if st.button("🇺🇸 Load US Companies", use_container_width=True):
        with st.spinner("Fetching US tickers..."):
            try:
                ok = populate_companies(con, "US", test_mode=not full_universe)
                if ok:
                    cursor = con.cursor()
                    cursor.execute("SELECT COUNT(*) FROM companies WHERE market = 'US'")
                    count = cursor.fetchone()[0]
                    st.success(f"✅ Loaded US companies. Total US tickers in DB: {count}")
                else:
                    st.error("❌ Failed to load US companies. Check logs below for details.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

with col2:
    if st.button("🇮🇳 Load India Companies", use_container_width=True):
        with st.spinner("Fetching India tickers..."):
            try:
                ok = populate_companies(con, "IN", test_mode=not full_universe)
                if ok:
                    cursor = con.cursor()
                    cursor.execute("SELECT COUNT(*) FROM companies WHERE market = 'IN'")
                    count = cursor.fetchone()[0]
                    st.success(f"✅ Loaded India companies. Total India tickers in DB: {count}")
                else:
                    st.error("❌ Failed to load India companies. Check logs below for details.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# Show current universe size
cursor = con.cursor()
cursor.execute("SELECT market, COUNT(*) FROM companies GROUP BY market")
universe_counts = dict(cursor.fetchall())
if universe_counts:
    st.info(f"📊 Current universe: " + " | ".join(f"{m}: {c}" for m, c in universe_counts.items()))
else:
    st.warning("⚠️ No companies loaded yet. Click a button above to get started.")

st.divider()

# ============================================================================
# STEP 2: REFRESH PRICES & TECHNICALS
# ============================================================================
st.subheader("2. Refresh Prices & Technicals")
st.caption("Fetches historical prices and computes moving averages, RSI, MACD, etc. Required before running any strategy.")

col1, col2, col3 = st.columns(3)
with col1:
    price_market = st.selectbox("Market", ["US", "IN", "ALL"], key="price_market")
with col2:
    price_period = st.selectbox("History period", ["1y", "2y", "5y"], index=1,
                                help="220 EMA / SMA220 strategies need at least 2y of data.")
with col3:
    st.write("")
    st.write("")
    run_refresh = st.button("▶️ Refresh Prices", type="primary", use_container_width=True)

if run_refresh:
    progress_bar = st.progress(0)
    status_text = st.empty()

    def progress_callback(current, total, status):
        progress_bar.progress(min(current / max(total, 1), 1.0))
        status_text.text(f"{status} ({current}/{total})")

    try:
        with st.spinner("Refreshing prices and technicals... this can take a while for large universes."):
            stats = refresh_prices(con, market=price_market, period=price_period,
                                  progress_callback=progress_callback)
        progress_bar.progress(1.0)
        st.success(f"✅ Done. Attempted: {stats['attempted']}, Succeeded: {stats['succeeded']}, Failed: {stats['failed']}")
    except Exception as e:
        st.error(f"❌ Error refreshing prices: {e}")

# Show current technicals coverage
cursor.execute("SELECT COUNT(*) FROM technicals_latest")
tech_count = cursor.fetchone()[0]
st.info(f"📈 Stocks with computed technicals: {tech_count}")

st.divider()

# ============================================================================
# STEP 3: REFRESH INDIA FUNDAMENTALS (SCREENER.IN)
# ============================================================================
st.subheader("3. Refresh India Fundamentals (Screener.in)")
st.caption("Scrapes Ratios, P&L, Balance Sheet, Cash Flow, and Shareholding Pattern for India "
          "stocks. Runs one request per ticker with a short delay between each — refreshing the "
          "full universe can take a while.")

col1, col2 = st.columns([3, 1])
with col1:
    fundamentals_scope = st.radio(
        "Scope", ["All India tickers with fundamentals coverage", "Specific tickers"],
        horizontal=True, key="fundamentals_scope",
    )
    specific_tickers = None
    if fundamentals_scope == "Specific tickers":
        tickers_input = st.text_input(
            "Tickers (comma-separated, e.g. RELIANCE.NS, TCS.NS)", key="fundamentals_tickers_input"
        )
        specific_tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()] or None
with col2:
    st.write("")
    st.write("")
    run_fundamentals_refresh = st.button("🇮🇳 Refresh Fundamentals", width="stretch")

if run_fundamentals_refresh:
    progress_bar = st.progress(0)
    status_text = st.empty()

    def fundamentals_progress_callback(current, total, status):
        progress_bar.progress(min(current / max(total, 1), 1.0))
        status_text.text(f"{status} ({current}/{total})")

    try:
        with st.spinner("Refreshing India fundamentals from Screener.in..."):
            stats = refresh_india_fundamentals(con, tickers=specific_tickers,
                                              progress_callback=fundamentals_progress_callback)
        progress_bar.progress(1.0)
        st.success(f"✅ Done. Attempted: {stats['attempted']}, Succeeded: {stats['succeeded']}, Failed: {stats['failed']}")
        if stats["failed_tickers"]:
            st.warning(f"Failed: {', '.join(stats['failed_tickers'])}")
    except Exception as e:
        st.error(f"❌ Error refreshing fundamentals: {e}")

cursor.execute("SELECT COUNT(DISTINCT ticker) FROM fundamentals_latest")
fund_count = cursor.fetchone()[0]
st.info(f"📋 India stocks with fundamentals loaded: {fund_count}")

st.divider()

# ============================================================================
# REFRESH STATUS LOG
# ============================================================================
st.subheader("Refresh History")

try:
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
        st.info("📦 No refresh history yet. Use the buttons above to load data.")
except Exception:
    st.info("📦 No refresh history yet. Use the buttons above to load data.")

st.divider()
st.subheader("India Fundamentals Note")
st.info("""
🇮🇳 **Coverage**: India fundamentals come from Screener.in and are only fetched for tickers with
`has_fundamentals=1` (currently the tickers loaded via "Load India Companies" above).
Cash Flow is annual-only — Indian companies don't disclose a quarterly cash flow statement.
""")

con.close()
