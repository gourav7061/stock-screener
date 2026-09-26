#!/usr/bin/env python
"""Migrate legacy strategies from prototype to new AND/OR schema."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))

from stockscreener.db import get_connection, init_db
from stockscreener.strategy_engine import migrate_legacy_strategy, save_strategy
from stockscreener.config import DB_PATH


def main():
    # Initialize DB
    init_db(DB_PATH)
    con = get_connection(DB_PATH)

    # Legacy strategy data (from the prototype)
    legacy_strategies = [
        {
            "name": "Golden Cross Momentum",
            "conditions": [
                {"metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma200", "value": 0.0},
                {"metric": "price", "operator": ">", "compare_type": "metric", "compare_metric": "sma50", "value": 0.0},
                {"metric": "pct_change_1m", "operator": ">", "compare_type": "value", "value": 3.0}
            ]
        },
        {
            "name": "Oversold Value Pick",
            "conditions": [
                {"metric": "rsi14", "operator": "<", "compare_type": "value", "value": 35.0},
                {"metric": "pe_ratio", "operator": "<", "compare_type": "value", "value": 25.0}
            ]
        }
    ]

    print("Migrating legacy strategies to new AND/OR schema...")

    for legacy in legacy_strategies:
        # Migrate to new schema
        migrated = migrate_legacy_strategy(legacy)

        # Save to DB
        strategy_id = save_strategy(con, migrated)

        print(f"  ✓ {migrated['name']} (ID: {strategy_id})")

    con.close()

    print("\n✓ Migration complete")


if __name__ == "__main__":
    main()
