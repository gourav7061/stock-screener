"""Strategy Builder page — create strategies in plain English or raw JSON."""

import streamlit as st
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stockscreener.db import init_db, get_connection
from stockscreener.config import DB_PATH
from stockscreener.strategy_engine import list_strategies, load_strategy, save_strategy, validate_strategy, describe_node
from stockscreener.metrics import get_metrics_registry, BUILT_IN_METRICS
from stockscreener.nl_parser import parse_conditions_text

st.set_page_config(page_title="Strategy Builder", layout="wide")
st.title("🛠️ Strategy Builder")
st.markdown("Describe your strategy in plain English, or drop into raw JSON if you need full control.")

# A value staged here gets copied into the JSON editor's session state at the
# top of the *next* run — widgets can't have their session-state key written
# to after they've already been instantiated in the same run.
if "_pending_strategy_json" in st.session_state:
    st.session_state["strategy_json_editor"] = st.session_state.pop("_pending_strategy_json")

# Initialize database
try:
    init_db(DB_PATH)
except Exception:
    pass

con = get_connection(DB_PATH)
try:
    metrics_registry = get_metrics_registry(con)
except Exception:
    metrics_registry = BUILT_IN_METRICS.copy()

DEFAULT_NL_CONDITIONS = """150 SMA > 220 EMA
Price(Close) > 50 SMA
50 SMA > 150 SMA
Price(Close) > 1.25*52 week low
Stock must have dipped below 220 EMA at least once in the past 90 trading days"""

DEFAULT_JSON_TEMPLATE = """{
  "name": "My Strategy",
  "root": {
    "logic": "AND",
    "items": [
      {
        "metric": "sma50",
        "operator": ">",
        "compare_type": "metric",
        "compare_metric": "sma200"
      }
    ]
  }
}"""

if "strategy_json_editor" not in st.session_state:
    st.session_state["strategy_json_editor"] = DEFAULT_JSON_TEMPLATE

# Tabs
tab_nl, tab_json, tab_saved, tab_metrics = st.tabs(
    ["✍️ Plain English", "🧩 Advanced (JSON)", "📁 Saved Strategies", "📊 Available Metrics"]
)

# ============================================================================
# TAB: PLAIN ENGLISH
# ============================================================================
with tab_nl:
    st.subheader("1. Describe your conditions")
    st.markdown(
        "Write one condition per line. Mix and match wording — the system understands "
        "things like `150 SMA > 220 EMA`, `Price above 50 SMA`, `RSI < 35`, "
        "`Price > 1.25 * 52 week low`, and `Stock dipped below 220 EMA in the past 90 trading days`."
    )

    with st.expander("📖 Supported phrasing cheat sheet"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                "**Metrics**\n"
                "- `150 SMA`, `220 EMA` (any tracked period: 20/50/150/200/220)\n"
                "- `Price`, `Price(Close)`, `Close`\n"
                "- `52 week low`\n"
                "- `RSI`, `RSI(14)`\n"
                "- `P/E`, `Forward P/E`, `P/B`\n"
                "- `Debt to Equity`, `ROE`, `Profit Margin`\n"
                "- `Dividend Yield`, `Market Cap`, `Volume`\n"
                "- `1 Month % Change` / `3 Month % Change` / `1 Year % Change`"
            )
        with col_b:
            st.markdown(
                "**Operators & phrases**\n"
                "- `>`, `<`, `>=`, `<=`, `==`, `!=`\n"
                "- `greater than`, `more than`, `above`, `exceeds`\n"
                "- `less than`, `below`, `under`\n"
                "- `at least` (>=), `at most` (<=)\n"
                "\n**Multipliers**\n"
                "- `1.25 * 52 week low`\n"
                "- `25% above 52 week low`\n"
                "\n**Historical dip check**\n"
                "- `Stock dipped below 220 EMA in the past 90 trading days`"
            )

    strategy_name = st.text_input("Strategy Name", value="My Strategy", key="nl_strategy_name")
    conditions_text = st.text_area(
        "Conditions (one per line)",
        value=DEFAULT_NL_CONDITIONS,
        height=200,
        key="nl_conditions_text",
    )

    if st.button("🔍 Translate to Strategy", type="primary"):
        root, parse_errors = parse_conditions_text(conditions_text, metrics_registry)
        st.session_state["nl_parsed_root"] = root
        st.session_state["nl_parse_errors"] = parse_errors

    if "nl_parsed_root" in st.session_state:
        root = st.session_state["nl_parsed_root"]
        parse_errors = st.session_state["nl_parse_errors"]

        st.divider()
        st.subheader("2. Review the translation")

        if parse_errors:
            st.error(f"⚠️ {len(parse_errors)} line(s) couldn't be understood and were skipped:")
            for err in parse_errors:
                st.write(f"  • Line {err['line_number']}: `{err['line'].strip()}` — {err['reason']}")

        items = root.get("items", [])
        if items:
            st.success(f"✅ Understood {len(items)} condition(s):")
            for item in items:
                st.write(f"  • {describe_node(item, metrics_registry)}")

        with st.expander("View generated JSON"):
            st.json({"name": strategy_name, "root": root})

        strategy = {"name": strategy_name, "root": root}
        validation_errors = validate_strategy(strategy, metrics_registry) if items else ["No conditions were understood"]

        if validation_errors:
            st.warning("This strategy isn't ready to save yet:")
            for e in validation_errors:
                st.write(f"  • {e}")
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Strategy", type="primary", use_container_width=True, key="nl_save"):
                    try:
                        strategy_id = save_strategy(con, strategy)
                        st.success(f"✅ Strategy '{strategy_name}' saved (ID: {strategy_id})")
                        st.info("Go to 'Run Screener' to test it")
                    except Exception as e:
                        st.error(f"Error saving strategy: {str(e)}")
            with col2:
                if st.button("🧩 Send to Advanced JSON editor", use_container_width=True, key="nl_send_json"):
                    st.session_state["_pending_strategy_json"] = json.dumps(strategy, indent=2)
                    st.rerun()

# ============================================================================
# TAB: ADVANCED (JSON)
# ============================================================================
with tab_json:
    st.subheader("Define Your Strategy in JSON")
    st.caption("For full control over nested AND/OR groups and multi-condition tuning.")

    try:
        existing = list_strategies(con)
    except Exception:
        existing = []

    load_choice = st.selectbox(
        "Load existing strategy (optional)",
        ["-- New Strategy --"] + [s["name"] for s in existing],
        key="strategy_load_choice",
    )

    if load_choice != st.session_state.get("_last_load_choice"):
        st.session_state["_last_load_choice"] = load_choice
        if load_choice != "-- New Strategy --":
            loaded = load_strategy(con, next(s["id"] for s in existing if s["name"] == load_choice))
            st.session_state["_pending_strategy_json"] = json.dumps(loaded, indent=2)
            st.rerun()

    st.markdown("**Paste or edit your strategy JSON:**")
    strategy_text = st.text_area(
        "Strategy Definition",
        height=300,
        label_visibility="collapsed",
        key="strategy_json_editor",
    )

    # Parse and validate
    if strategy_text.strip():
        try:
            strategy = json.loads(strategy_text)
            errors = validate_strategy(strategy, metrics_registry)

            if errors:
                st.error("❌ Validation Errors:")
                for error in errors:
                    st.write(f"  • {error}")
            else:
                st.success("✅ Strategy is valid!")

                # Save button
                if st.button("💾 Save Strategy", type="primary", use_container_width=True, key="json_save"):
                    try:
                        strategy_id = save_strategy(con, strategy)
                        st.success(f"✅ Strategy '{strategy['name']}' saved successfully (ID: {strategy_id})")
                        st.info("Go to 'Run Screener' tab to test your strategy")
                    except Exception as e:
                        st.error(f"Error saving strategy: {str(e)}")
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON: {str(e)}")

# ============================================================================
# TAB: SAVED STRATEGIES
# ============================================================================
with tab_saved:
    st.subheader("Your Saved Strategies")

    try:
        strategies = list_strategies(con)
        if strategies:
            for strategy in strategies:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{strategy['name']}**")
                    st.caption(f"ID: {strategy['id']} | Updated: {strategy['updated_at'][:10]}")
                with col2:
                    if st.button("📋 View", key=f"view_{strategy['id']}"):
                        loaded = load_strategy(con, strategy['id'])
                        st.json(loaded)
        else:
            st.info("No strategies saved yet. Create one in the 'Plain English' tab!")
    except Exception as e:
        st.info("No strategies saved yet. Create one in the 'Plain English' tab!")

# ============================================================================
# TAB: AVAILABLE METRICS
# ============================================================================
with tab_metrics:
    st.subheader("Available Metrics (60+)")
    st.markdown("Reference these when writing plain-English conditions or JSON.")

    # Group by category
    categories = {}
    for key, info in sorted(metrics_registry.items()):
        cat = info.get("category", "Other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((key, info["label"]))

    # Display by category
    for category in sorted(categories.keys()):
        with st.expander(f"📊 {category}", expanded=(category == "Technical")):
            for key, label in sorted(categories[category]):
                st.code(key, language="text")
                st.caption(label)

# ============================================================================
# EXAMPLES SECTION
# ============================================================================
st.divider()
st.subheader("📚 Strategy Examples")

examples = {
    "220 EMA Breakout (Your Strategy)": {
        "name": "220 EMA Breakout",
        "root": {
            "logic": "AND",
            "items": [
                {"metric": "sma150", "operator": ">", "compare_type": "metric", "compare_metric": "ema220"},
                {"metric": "price", "operator": ">", "compare_type": "metric", "compare_metric": "sma50"},
                {"metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma150"},
                {"metric": "price", "operator": ">", "compare_type": "metric", "compare_metric": "52w_low", "multiplier": 1.25},
                {"condition_type": "dipped_below", "compare_level": "ema220", "days": 90}
            ]
        }
    },
    "Golden Cross": {
        "name": "Golden Cross Momentum",
        "root": {
            "logic": "AND",
            "items": [
                {"metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma200"},
                {"metric": "price", "operator": ">", "compare_type": "metric", "compare_metric": "sma50"},
                {"metric": "pct_change_1m", "operator": ">", "compare_type": "value", "value": 3.0}
            ]
        }
    },
    "Oversold Value Pick": {
        "name": "Oversold Value Pick",
        "root": {
            "logic": "AND",
            "items": [
                {"metric": "rsi14", "operator": "<", "compare_type": "value", "value": 35.0},
                {"metric": "pe_ratio", "operator": "<", "compare_type": "value", "value": 25.0}
            ]
        }
    },
    "Mean Reversion": {
        "name": "Mean Reversion Setup",
        "root": {
            "logic": "AND",
            "items": [
                {"metric": "rsi14", "operator": "<", "compare_type": "value", "value": 30.0},
                {"metric": "pct_change_1m", "operator": "<", "compare_type": "value", "value": -10.0},
                {"metric": "bb_percent_b", "operator": "<", "compare_type": "value", "value": 0.2}
            ]
        }
    }
}

cols = st.columns(2)
for idx, (name, strategy) in enumerate(examples.items()):
    with cols[idx % 2]:
        with st.expander(f"📌 {name}"):
            st.json(strategy)
            if st.button("Load into Advanced JSON tab", key=f"example_{idx}"):
                st.session_state["_pending_strategy_json"] = json.dumps(strategy, indent=2)
                st.rerun()

con.close()
