"""Strategy Builder page — create flexible AND/OR strategies with JSON."""

import streamlit as st
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stockscreener.db import init_db, get_connection
from stockscreener.config import DB_PATH
from stockscreener.strategy_engine import list_strategies, load_strategy, save_strategy, validate_strategy
from stockscreener.metrics import get_metrics_registry, BUILT_IN_METRICS

st.set_page_config(page_title="Strategy Builder", layout="wide")
st.title("🛠️ Strategy Builder")
st.markdown("Create flexible strategies with unlimited AND/OR logic conditions.")

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

# Tabs
tab1, tab2, tab3 = st.tabs(["Create Strategy", "Saved Strategies", "Available Metrics"])

# ============================================================================
# TAB 1: CREATE STRATEGY
# ============================================================================
with tab1:
    st.subheader("1. Define Your Strategy")

    # Load existing strategy
    try:
        existing = list_strategies(con)
    except:
        existing = []

    col1, col2 = st.columns(2)
    with col1:
        load_choice = st.selectbox(
            "Load existing strategy (optional)",
            ["-- New Strategy --"] + [s["name"] for s in existing]
        )

    if load_choice != "-- New Strategy --":
        loaded = load_strategy(con, next(s["id"] for s in existing if s["name"] == load_choice))
        strategy_json = json.dumps(loaded, indent=2)
    else:
        strategy_json = """{
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

    st.markdown("**Paste or edit your strategy JSON:**")
    strategy_text = st.text_area(
        "Strategy Definition",
        value=strategy_json,
        height=300,
        label_visibility="collapsed"
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
                if st.button("💾 Save Strategy", type="primary", use_container_width=True):
                    try:
                        strategy_id = save_strategy(con, strategy)
                        st.success(f"✅ Strategy '{strategy['name']}' saved successfully (ID: {strategy_id})")
                        st.info("Go to 'Run Screener' tab to test your strategy")
                    except Exception as e:
                        st.error(f"Error saving strategy: {str(e)}")
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON: {str(e)}")

# ============================================================================
# TAB 2: SAVED STRATEGIES
# ============================================================================
with tab2:
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
            st.info("No strategies saved yet. Create one in the 'Create Strategy' tab!")
    except Exception as e:
        st.info("No strategies saved yet. Create one in the 'Create Strategy' tab!")

# ============================================================================
# TAB 3: AVAILABLE METRICS
# ============================================================================
with tab3:
    st.subheader("Available Metrics (60+)")
    st.markdown("Use these metric names in your strategy JSON.")

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
                {"metric": "price", "operator": ">", "compare_type": "metric", "compare_metric": "52w_low_25pct"},
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
            if st.button(f"Use This Example", key=f"example_{idx}"):
                st.session_state.example_to_use = strategy
                st.info(f"Copied! Go to 'Create Strategy' tab and paste it.")

con.close()
