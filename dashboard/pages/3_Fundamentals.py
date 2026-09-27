"""Fundamentals page — Ratios, Profit & Loss, Cash Flow, and Shareholding Pattern."""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stockscreener.db import init_db, get_connection
from stockscreener.config import DB_PATH
from stockscreener import fundamentals_view as fv
from stockscreener.screener_in import refresh_company_fundamentals

st.set_page_config(page_title="Fundamentals", layout="wide")
st.title("📋 Fundamentals Analysis")

try:
    init_db(DB_PATH)
except Exception as e:
    st.error(f"⚠️ Database initialization/migration failed: {e}")
    st.caption("Fundamentals writes will likely fail until this is fixed — the table schema may be out of date.")

con = get_connection(DB_PATH)
cursor = con.cursor()

# ============================================================================
# SEARCH + PICK STOCK
# ============================================================================
cursor.execute("SELECT DISTINCT ticker, name FROM companies WHERE is_active = 1 ORDER BY ticker")
all_companies = [{"ticker": row[0], "name": row[1]} for row in cursor.fetchall()]

if not all_companies:
    st.info("No stocks in database yet")
    con.close()
    st.stop()

search_query = st.text_input("🔍 Search stock (name or ticker)", "", placeholder="e.g. Reliance, TCS, AAPL")

if search_query.strip():
    q = search_query.strip().lower()
    matches = [c for c in all_companies if q in c["ticker"].lower() or q in (c["name"] or "").lower()]
else:
    matches = all_companies

if not matches:
    st.warning(f"No stocks match '{search_query}'")
    con.close()
    st.stop()

ticker_display = st.selectbox(
    "Stock", [f"{c['ticker']} ({c['name']})" for c in matches],
)
ticker = ticker_display.split(" (")[0]

cursor.execute("SELECT market, name, has_fundamentals FROM companies WHERE ticker = ?", (ticker,))
stock_info = cursor.fetchone()
if not stock_info:
    st.error("Stock not found")
    con.close()
    st.stop()

market, name, has_fundamentals = stock_info
st.markdown(f"### {ticker} — {name}")

# ============================================================================
# INDIA: NEW 4-SECTION LAYOUT (Ratios / P&L / Cash Flow / Shareholding)
# ============================================================================
if market == "IN":
    if not has_fundamentals:
        st.warning(f"⚠️ Fundamentals not available for {ticker} (outside coverage tier)")
        st.info("🇮🇳 Indian fundamentals are only available for tickers marked `has_fundamentals=1`.")
        con.close()
        st.stop()

    has_data = fv.has_india_fundamentals(con, ticker)

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Refresh data" if has_data else "⬇️ Fetch fundamentals now", width="stretch"):
            with st.spinner(f"Fetching {ticker} from Screener.in..."):
                result = refresh_company_fundamentals(con, ticker)
            if result["success"]:
                st.success(f"✅ Updated ({result['line_items']} line items, {result['shareholding_periods']} shareholding periods)")
                st.rerun()
            else:
                st.error(f"❌ Failed: {result['error']}")

    if not has_data:
        st.info(f"No fundamentals data for {ticker} yet. Click 'Fetch fundamentals now' above.")
        con.close()
        st.stop()

    tab_ratios, tab_pl, tab_cf, tab_shp = st.tabs(
        ["📐 Ratios", "📈 Profit & Loss", "💰 Cash Flow", "🏛️ Shareholding Pattern"]
    )

    with tab_ratios:
        ratios = fv.get_ratios_snapshot(con, ticker)
        labels = list(ratios.keys())
        cols_per_row = 4
        for i in range(0, len(labels), cols_per_row):
            row_labels = labels[i:i + cols_per_row]
            cols = st.columns(cols_per_row)
            for col, label in zip(cols, row_labels):
                info = ratios[label]
                with col:
                    if info["available"]:
                        st.metric(label, info["value"])
                    else:
                        st.metric(label, "N/A", help=info["reason"])

    with tab_pl:
        period_type = st.radio("Period", ["Annual", "Quarterly"], horizontal=True, key="pl_period")
        df = fv.get_pl_table(con, ticker, period_type.lower())
        if df.empty:
            st.info("No Profit & Loss data available.")
        else:
            st.caption("Figures in ₹ Crores except EPS (₹) and Operating Profit % (%). "
                      "Annual view includes the last 5 fiscal years plus TTM (trailing twelve months).")
            st.dataframe(df, width="stretch")

    with tab_cf:
        period_type = st.radio("Period", ["Annual", "Quarterly"], horizontal=True, key="cf_period")
        df, note = fv.get_cash_flow_table(con, ticker, period_type.lower())
        if note:
            st.info(f"ℹ️ {note}")
        elif df is None or df.empty:
            st.info("No Cash Flow data available.")
        else:
            st.caption("Figures in ₹ Crores. Free Cash Flow isn't shown — Screener.in doesn't break out "
                      "CapEx on the main company page, so it can't be reliably computed yet.")
            st.dataframe(df, width="stretch")

    with tab_shp:
        period_type = st.radio("Period", ["Quarterly", "Annual"], horizontal=True, key="shp_period")
        df = fv.get_shareholding_table(con, ticker, period_type.lower())
        if df.empty:
            st.info("No Shareholding Pattern data available.")
        else:
            st.caption("Numbers in percentages. 'Others' combines Government + Public + any other "
                      "category beyond Promoter/FIIs/DIIs.")
            st.dataframe(df, width="stretch")

# ============================================================================
# US (AND ANY OTHER MARKET): FALLBACK RAW LINE-ITEM VIEW
# ============================================================================
else:
    st.info(
        "The Ratios / Profit & Loss / Cash Flow / Shareholding Pattern layout above is currently "
        "built for Indian stocks (via Screener.in). It hasn't been ported to US data yet — showing "
        "the raw SEC EDGAR line items below instead."
    )

    if not has_fundamentals:
        st.warning(f"⚠️ Fundamentals not available for {ticker} (outside coverage tier)")
    else:
        cursor.execute("""
            SELECT fiscal_period, period_end_date, line_item_key, line_item_label, value, unit, source
            FROM fundamentals WHERE ticker = ? ORDER BY period_end_date DESC
        """, (ticker,))
        rows = cursor.fetchall()

        if not rows:
            st.info(f"No fundamentals data for {ticker} yet. Run 'Data Refresh' to populate.")
        else:
            import pandas as pd

            line_items = {}
            for period, date, key, label, value, unit, source in rows:
                line_items.setdefault(key, {"label": label, "unit": unit, "data": []})
                line_items[key]["data"].append((period, date, value, source))

            for key, info in sorted(line_items.items(), key=lambda x: x[0]):
                with st.expander(f"{info['label']} ({info['unit'] or 'N/A'})"):
                    df_data = [
                        {"Period": period, "End Date": date, "Value": value, "Source": source}
                        for period, date, value, source in sorted(info["data"], key=lambda x: x[1] or "", reverse=True)[:10]
                    ]
                    st.dataframe(pd.DataFrame(df_data), width="stretch")

con.close()
