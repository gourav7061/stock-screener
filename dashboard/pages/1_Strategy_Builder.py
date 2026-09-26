"""Strategy Builder page — create/edit AND/OR strategies."""

import streamlit as st
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stockscreener.db import get_connection
from stockscreener.config import DB_PATH
from stockscreener.strategy_engine import list_strategies, load_strategy, save_strategy, validate_strategy, describe_node
from stockscreener.metrics import get_metrics_registry, OPERATORS

st.set_page_config(page_title="Strategy Builder", layout="wide")
st.title("🛠️ Strategy Builder")
st.markdown("Create no-code strategies with AND/OR logic.")

con = get_connection(DB_PATH)
metrics_registry = get_metrics_registry(con)

# Load/new strategy
st.subheader("1. Start")
existing = list_strategies(con)
load_choice = st.selectbox("Load existing strategy (optional)", ["-- New Strategy --"] + [s["name"] for s in existing])

if "strategy" not in st.session_state or st.session_state.get("loaded_from") != load_choice:
    if load_choice == "-- New Strategy --":
        st.session_state.strategy = {
            "name": "",
            "root": {"logic": "AND", "items": [{"metric": "rsi14", "operator": "<", "compare_type": "value", "value": 30.0}]}
        }
        st.session_state.strategy_name = ""
    else:
        loaded = load_strategy(con, next(s["id"] for s in existing if s["name"] == load_choice))
        st.session_state.strategy = loaded
        st.session_state.strategy_name = loaded["name"]

    st.session_state.loaded_from = load_choice

# Strategy name
st.subheader("2. Name")
st.session_state.strategy_name = st.text_input("Strategy name", value=st.session_state.strategy_name)

# Strategy editor (simplified flat AND/OR for v1)
st.subheader("3. Conditions")
st.markdown("*Note: v1 supports flat AND/OR of conditions. Nested groups coming in v2.*")

conditions = st.session_state.strategy.get("root", {}).get("items", [])
root_logic = st.session_state.strategy.get("root", {}).get("logic", "AND")

root_logic = st.radio("Combine conditions with", ["AND", "OR"], index=0 if root_logic == "AND" else 1)

metric_options = sorted(metrics_registry.keys())
metric_labels = {k: f"[{v['category']}] {v['label']}" for k, v in metrics_registry.items()}

to_remove = None
for i, cond in enumerate(conditions):
    cond.setdefault("compare_type", "value")

    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])

    with col1:
        cond["metric"] = st.selectbox(
            "Metric", metric_options,
            index=metric_options.index(cond.get("metric", "rsi14")),
            format_func=lambda k: metric_labels[k],
            key=f"metric_{i}"
        )

    with col2:
        cond["operator"] = st.selectbox(
            "Operator", list(OPERATORS.keys()),
            index=list(OPERATORS.keys()).index(cond.get("operator", ">")),
            key=f"op_{i}"
        )

    with col3:
        cond["compare_type"] = st.selectbox(
            "Compare to",
            ["value", "metric"],
            index=0 if cond.get("compare_type") == "value" else 1,
            format_func=lambda x: "fixed number" if x == "value" else "metric",
            key=f"comparetype_{i}"
        )

    with col4:
        if cond["compare_type"] == "value":
            cond["value"] = st.number_input("Value", value=float(cond.get("value", 0)), key=f"val_{i}")
        else:
            cond["compare_metric"] = st.selectbox(
                "Metric",
                metric_options,
                index=metric_options.index(cond.get("compare_metric", "sma50")),
                format_func=lambda k: metric_labels[k],
                key=f"comparemetric_{i}"
            )

    with col5:
        if st.button("🗑️", key=f"del_{i}"):
            to_remove = i

if to_remove is not None:
    conditions.pop(to_remove)
    st.rerun()

if st.button("➕ Add condition"):
    conditions.append({"metric": "price", "operator": ">", "compare_type": "value", "value": 0.0})
    st.rerun()

# Update strategy
st.session_state.strategy["root"]["logic"] = root_logic
st.session_state.strategy["root"]["items"] = conditions
st.session_state.strategy["name"] = st.session_state.strategy_name

# Preview
st.subheader("4. Preview")
if conditions:
    preview = describe_node(st.session_state.strategy["root"], metrics_registry)
    st.markdown(f"**Will screen for**: {preview}")

# Validate & save
st.subheader("5. Save")
if st.button("💾 Save Strategy", type="primary"):
    if not st.session_state.strategy_name.strip():
        st.error("Strategy must have a name")
    elif not conditions:
        st.error("Strategy must have at least one condition")
    else:
        # Validate
        errors = validate_strategy(st.session_state.strategy, metrics_registry)
        if errors:
            st.error(f"Validation errors:\n" + "\n".join(errors))
        else:
            strategy_id = save_strategy(con, st.session_state.strategy)
            st.success(f"✅ Strategy saved (ID: {strategy_id})")
            st.info("Go to 'Run Screener' to execute it")

con.close()
