"""Strategy engine with AND/OR logic."""

import sqlite3
import json
import operator
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from .metrics import get_metrics_registry, OPERATORS


def is_group(node: dict) -> bool:
    """Check if a node is a group (has 'logic' key) vs a condition leaf (has 'metric' key)."""
    return "logic" in node


def evaluate_condition(cond: dict, values: Dict[str, float], con: sqlite3.Connection = None) -> bool:
    """Evaluate a single condition against values dict. Returns False if any operand is missing.

    Special condition types:
    - "dipped_below": Check if price dipped below a level in past N days (requires con and ticker)
    """
    condition_type = cond.get("condition_type", "simple")

    if condition_type == "dipped_below":
        return _evaluate_dipped_below(cond, values, con)

    # Standard comparison condition
    metric_key = cond.get("metric")
    operator_sym = cond.get("operator")
    compare_type = cond.get("compare_type", "value")

    if metric_key not in values:
        return False

    val = values[metric_key]
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False

    if compare_type == "metric":
        compare_metric_key = cond.get("compare_metric")
        if compare_metric_key not in values:
            return False
        target = values[compare_metric_key]
        if target is None or (isinstance(target, float) and pd.isna(target)):
            return False
    else:  # "value"
        target = cond.get("value")

    # Map operator symbol to function
    op_func = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
    }.get(operator_sym)

    if not op_func:
        return False

    try:
        return op_func(val, target)
    except (TypeError, ValueError):
        return False


def _evaluate_dipped_below(cond: dict, values: Dict[str, float], con: sqlite3.Connection) -> bool:
    """Check if price dipped below a threshold in past N trading days.

    Condition format:
    {
        "condition_type": "dipped_below",
        "compare_level": "ema220",  # metric to check against, or "value" if using static value
        "threshold_value": 100.5,   # if compare_level is a static value
        "days": 90,                 # number of trading days to lookback
        "ticker": "AAPL"            # ticker symbol
    }
    """
    if not con:
        return False

    ticker = values.get("ticker")
    if not ticker:
        return False

    compare_level = cond.get("compare_level")
    days = cond.get("days", 90)

    if compare_level == "value":
        threshold = cond.get("threshold_value")
    else:
        threshold = values.get(compare_level)

    if threshold is None:
        return False

    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM prices
            WHERE ticker = ?
            AND close < ?
            AND date >= date((SELECT MAX(date) FROM prices WHERE ticker = ?), '-' || ? || ' days')
        """, (ticker, threshold, ticker, days))

        result = cursor.fetchone()
        count = result[0] if result else 0
        return count > 0
    except (sqlite3.Error, TypeError, ValueError):
        return False


def evaluate_node(node: dict, values: Dict[str, float], con: sqlite3.Connection = None) -> bool:
    """Recursively evaluate a node (group or condition) against values dict."""
    if is_group(node):
        logic = node.get("logic", "AND").upper()
        items = node.get("items", [])

        if logic == "AND":
            return all(evaluate_node(item, values, con) for item in items)
        elif logic == "OR":
            return any(evaluate_node(item, values, con) for item in items)
        else:
            return False
    else:
        return evaluate_condition(node, values, con)


def describe_node(node: dict, metrics_registry: Dict) -> str:
    """Generate a human-readable description of a node."""
    if is_group(node):
        logic = node.get("logic", "AND").upper()
        items = node.get("items", [])

        descriptions = [describe_node(item, metrics_registry) for item in items]

        if logic == "AND":
            return " AND ".join([f"({d})" if is_group(item) else d for d, item in zip(descriptions, items)])
        elif logic == "OR":
            return " OR ".join([f"({d})" if is_group(item) else d for d, item in zip(descriptions, items)])
        else:
            return ""
    else:
        cond = node
        metric_key = cond.get("metric")
        operator_sym = cond.get("operator")
        compare_type = cond.get("compare_type", "value")

        label = metrics_registry.get(metric_key, {}).get("label", metric_key)
        op_text = OPERATORS.get(operator_sym, operator_sym)

        if compare_type == "metric":
            compare_metric_key = cond.get("compare_metric")
            target_label = metrics_registry.get(compare_metric_key, {}).get("label", compare_metric_key)
            return f"{label} {op_text} {target_label}"
        else:
            value = cond.get("value")
            return f"{label} {op_text} {value}"


def validate_strategy(strategy: dict, metrics_registry: Dict, max_depth: int = 5) -> List[str]:
    """Validate a strategy for errors. Returns list of error messages (empty if valid)."""
    errors = []

    if "name" not in strategy or not strategy["name"].strip():
        errors.append("Strategy must have a non-empty name")

    if "root" not in strategy:
        errors.append("Strategy must have a root node")
        return errors

    def validate_node(node: dict, depth: int = 0):
        if depth > max_depth:
            errors.append(f"Strategy nesting exceeds maximum depth of {max_depth}")
            return

        if is_group(node):
            logic = node.get("logic", "").upper()
            if logic not in ("AND", "OR"):
                errors.append(f"Invalid logic operator: {logic}")

            items = node.get("items", [])
            if not items:
                errors.append("Strategy group must have at least one item")

            for item in items:
                validate_node(item, depth + 1)
        else:
            metric_key = node.get("metric")
            if metric_key not in metrics_registry:
                errors.append(f"Unknown metric: {metric_key}")

            operator_sym = node.get("operator")
            if operator_sym not in OPERATORS:
                errors.append(f"Invalid operator: {operator_sym}")

            compare_type = node.get("compare_type", "value")
            if compare_type == "metric":
                compare_metric_key = node.get("compare_metric")
                if compare_metric_key not in metrics_registry:
                    errors.append(f"Unknown compare metric: {compare_metric_key}")
            elif compare_type != "value":
                errors.append(f"Invalid compare_type: {compare_type}")

    validate_node(strategy["root"])
    return errors


def migrate_legacy_strategy(old_strategy: dict) -> dict:
    """Migrate prototype's flat {'name', 'conditions'} schema to new recursive schema."""
    return {
        "name": old_strategy.get("name"),
        "root": {
            "logic": "AND",
            "items": old_strategy.get("conditions", [])
        }
    }


def list_strategies(con: sqlite3.Connection) -> List[Dict]:
    """List all saved strategies."""
    cursor = con.cursor()
    cursor.execute("SELECT id, name, created_at, updated_at FROM strategies ORDER BY updated_at DESC")
    return [dict(row) for row in cursor.fetchall()]


def load_strategy(con: sqlite3.Connection, strategy_id: int) -> Dict:
    """Load a strategy by ID."""
    cursor = con.cursor()
    cursor.execute("SELECT id, name, definition_json FROM strategies WHERE id = ?", (strategy_id,))
    row = cursor.fetchone()

    if not row:
        return None

    strategy = dict(row)
    strategy["root"] = json.loads(strategy["definition_json"])
    del strategy["definition_json"]
    return strategy


def save_strategy(con: sqlite3.Connection, strategy: Dict) -> int:
    """Save or update a strategy. Returns the strategy ID."""
    now = datetime.utcnow().isoformat()
    root = strategy.get("root", {})
    definition_json = json.dumps(root)

    cursor = con.cursor()

    try:
        # Check if strategy already exists by name
        cursor.execute("SELECT id FROM strategies WHERE name = ?", (strategy["name"],))
        existing = cursor.fetchone()

        if existing:
            strategy_id = existing[0]
            cursor.execute("""
                UPDATE strategies SET definition_json = ?, updated_at = ?
                WHERE id = ?
            """, (definition_json, now, strategy_id))
        else:
            cursor.execute("""
                INSERT INTO strategies (name, definition_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (strategy["name"], definition_json, now, now))
            strategy_id = cursor.lastrowid

        con.commit()
        return strategy_id
    except sqlite3.OperationalError as e:
        if "strategies" in str(e):
            # Table doesn't exist, try to create it
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    definition_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            con.commit()
            # Retry the insert
            cursor.execute("""
                INSERT INTO strategies (name, definition_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (strategy["name"], definition_json, now, now))
            strategy_id = cursor.lastrowid
            con.commit()
            return strategy_id
        else:
            raise


def delete_strategy(con: sqlite3.Connection, strategy_id: int) -> None:
    """Delete a strategy by ID."""
    cursor = con.cursor()
    cursor.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))
    con.commit()


def run_strategy_against_db(con: sqlite3.Connection, strategy: Dict, tickers: List[str],
                           metrics_registry: Dict = None) -> pd.DataFrame:
    """Run a strategy against cached data for a list of tickers.

    Returns a DataFrame of matching tickers with their metric values.
    """
    if metrics_registry is None:
        metrics_registry = get_metrics_registry(con)

    # Fetch technical data
    placeholders = ",".join(["?" for _ in tickers])
    cursor = con.cursor()
    cursor.execute(f"SELECT * FROM technicals_latest WHERE ticker IN ({placeholders})", tickers)
    tech_rows = {row[0]: dict(row) for row in cursor.fetchall()}

    # Fetch fundamental latest data
    cursor.execute(f"SELECT * FROM fundamentals_latest WHERE ticker IN ({placeholders})", tickers)
    fund_rows = {row[0]: dict(row) for row in cursor.fetchall()}

    # Get the line item keys needed for custom fundamentals
    fundamental_keys = {k for k, v in metrics_registry.items() if v.get("category") == "Fundamental"}
    custom_keys = [k for k in fundamental_keys if k not in fund_rows.get(tickers[0], {})]

    # Run strategy evaluation
    matches = []
    for ticker in tickers:
        if ticker not in tech_rows:
            continue

        # Combine technical + fundamental data
        values = {**tech_rows[ticker]}
        if ticker in fund_rows:
            values.update(fund_rows[ticker])

        # Fetch latest custom fundamentals
        for key in custom_keys:
            cursor.execute("""
                SELECT value FROM fundamentals
                WHERE ticker = ? AND line_item_key = ?
                ORDER BY period_end_date DESC LIMIT 1
            """, (ticker, key))
            row = cursor.fetchone()
            if row:
                values[key] = row[0]

        # Evaluate strategy
        values["ticker"] = ticker
        if evaluate_node(strategy.get("root", {}), values, con):
            row_data = {"Ticker": ticker}
            row_data.update(values)
            matches.append(row_data)

    if not matches:
        return pd.DataFrame()

    df = pd.DataFrame(matches)

    # Rename columns to friendly names
    rename_map = {k: v.get("label", k) for k, v in metrics_registry.items()}
    df = df.rename(columns=rename_map)

    return df
