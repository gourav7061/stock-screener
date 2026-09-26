"""Example strategies demonstrating flexible condition definitions."""

import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from stockscreener.db import get_connection
from stockscreener.strategy_engine import save_strategy, validate_strategy, run_strategy_against_db
from stockscreener.metrics import get_metrics_registry


def create_220_ema_breakout_strategy():
    """220 EMA Breakout Strategy with 5 conditions.

    Conditions:
    1. 150SMA > 220EMA
    2. Price(Close) > 50SMA
    3. 50SMA > 150SMA
    4. Price(Close) > 1.25 * 52-week low (25% above 52-week low)
    5. Stock must have dipped below 220 EMA at least once in the past 90 trading days
    """
    strategy = {
        "name": "220 EMA Breakout",
        "root": {
            "logic": "AND",
            "items": [
                # Condition 1: 150SMA > 220EMA
                {
                    "metric": "sma150",
                    "operator": ">",
                    "compare_type": "metric",
                    "compare_metric": "ema220"
                },
                # Condition 2: Price > 50SMA
                {
                    "metric": "price",
                    "operator": ">",
                    "compare_type": "metric",
                    "compare_metric": "sma50"
                },
                # Condition 3: 50SMA > 150SMA
                {
                    "metric": "sma50",
                    "operator": ">",
                    "compare_type": "metric",
                    "compare_metric": "sma150"
                },
                # Condition 4: Price > 1.25 * 52-week low
                {
                    "metric": "price",
                    "operator": ">",
                    "compare_type": "metric",
                    "compare_metric": "52w_low_25pct"
                },
                # Condition 5: Stock dipped below 220 EMA in past 90 days
                {
                    "condition_type": "dipped_below",
                    "compare_level": "ema220",
                    "days": 90
                }
            ]
        }
    }
    return strategy


def create_golden_cross_strategy():
    """Golden Cross: SMA50 > SMA200 AND Price > SMA50 AND 1-month positive."""
    strategy = {
        "name": "Golden Cross Momentum",
        "root": {
            "logic": "AND",
            "items": [
                {
                    "metric": "sma50",
                    "operator": ">",
                    "compare_type": "metric",
                    "compare_metric": "sma200"
                },
                {
                    "metric": "price",
                    "operator": ">",
                    "compare_type": "metric",
                    "compare_metric": "sma50"
                },
                {
                    "metric": "pct_change_1m",
                    "operator": ">",
                    "compare_type": "value",
                    "value": 3.0
                }
            ]
        }
    }
    return strategy


def create_value_pick_strategy():
    """Value Pick: Low RSI and low P/E ratio."""
    strategy = {
        "name": "Oversold Value Pick",
        "root": {
            "logic": "AND",
            "items": [
                {
                    "metric": "rsi14",
                    "operator": "<",
                    "compare_type": "value",
                    "value": 35.0
                },
                {
                    "metric": "pe_ratio",
                    "operator": "<",
                    "compare_type": "value",
                    "value": 25.0
                }
            ]
        }
    }
    return strategy


def save_example_strategies(db_path="data/stockscreener.db"):
    """Save example strategies to the database."""
    con = get_connection(db_path)
    metrics_registry = get_metrics_registry(con)

    strategies = [
        create_220_ema_breakout_strategy(),
        create_golden_cross_strategy(),
        create_value_pick_strategy(),
    ]

    for strategy in strategies:
        errors = validate_strategy(strategy, metrics_registry)
        if errors:
            print(f"❌ {strategy['name']}:")
            for error in errors:
                print(f"   - {error}")
        else:
            strategy_id = save_strategy(con, strategy)
            print(f"✅ {strategy['name']} (ID: {strategy_id})")
            print(f"   JSON: {json.dumps(strategy, indent=2)}")
            print()


def list_available_metrics(db_path="data/stockscreener.db"):
    """Print all available metrics for building conditions."""
    con = get_connection(db_path)
    metrics = get_metrics_registry(con)

    print("\n" + "="*70)
    print("AVAILABLE METRICS FOR CONDITIONS")
    print("="*70)

    # Group by category
    categories = {}
    for key, info in metrics.items():
        cat = info.get("category", "Other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((key, info["label"]))

    for cat in sorted(categories.keys()):
        print(f"\n📊 {cat}")
        print("-" * 70)
        for key, label in sorted(categories[cat]):
            print(f"  • {key:25} → {label}")


def print_strategy_syntax():
    """Print documentation on how to define strategies."""
    doc = """
╔════════════════════════════════════════════════════════════════════════════╗
║                    FLEXIBLE STRATEGY BUILDER GUIDE                         ║
╚════════════════════════════════════════════════════════════════════════════╝

BASIC STRUCTURE:
  {
    "name": "Your Strategy Name",
    "root": {
      "logic": "AND",  // or "OR"
      "items": [
        { condition }, { condition }, ...
      ]
    }
  }

SIMPLE CONDITIONS (compare two values):
  {
    "metric": "price",
    "operator": ">",             // >, <, >=, <=, ==, !=
    "compare_type": "value",
    "value": 100.5
  }

METRIC-TO-METRIC CONDITIONS (compare two metrics):
  {
    "metric": "sma50",
    "operator": ">",
    "compare_type": "metric",
    "compare_metric": "sma200"
  }

HISTORICAL CONDITIONS (check if price dipped below level in past N days):
  {
    "condition_type": "dipped_below",
    "compare_level": "ema220",    // metric to check against
    "days": 90                      // lookback period in trading days
  }

NESTING (combine with AND/OR):
  {
    "logic": "OR",
    "items": [
      { condition1 },
      {
        "logic": "AND",
        "items": [ { condition2 }, { condition3 } ]
      }
    ]
  }

OPERATORS:
  >   is greater than
  <   is less than
  >=  is greater than or equal to
  <=  is less than or equal to
  ==  is equal to
  !=  is not equal to

EXAMPLE: 220 EMA Breakout Strategy
  Conditions:
  1. 150SMA > 220EMA
  2. Price > 50SMA
  3. 50SMA > 150SMA
  4. Price > 1.25 * 52-week low
  5. Price dipped below 220EMA in past 90 days

  Strategy JSON:
  {{
    "name": "220 EMA Breakout",
    "root": {{
      "logic": "AND",
      "items": [
        {{
          "metric": "sma150",
          "operator": ">",
          "compare_type": "metric",
          "compare_metric": "ema220"
        }},
        {{
          "metric": "price",
          "operator": ">",
          "compare_type": "metric",
          "compare_metric": "sma50"
        }},
        {{
          "metric": "sma50",
          "operator": ">",
          "compare_type": "metric",
          "compare_metric": "sma150"
        }},
        {{
          "metric": "price",
          "operator": ">",
          "compare_type": "metric",
          "compare_metric": "52w_low_25pct"
        }},
        {{
          "condition_type": "dipped_below",
          "compare_level": "ema220",
          "days": 90
        }}
      ]
    }}
  }}
"""
    print(doc)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Example strategies for stock screening")
    parser.add_argument("--save", action="store_true", help="Save example strategies to database")
    parser.add_argument("--list-metrics", action="store_true", help="List all available metrics")
    parser.add_argument("--syntax", action="store_true", help="Print strategy syntax guide")
    parser.add_argument("--db", default="data/stockscreener.db", help="Database path")

    args = parser.parse_args()

    if args.syntax:
        print_strategy_syntax()
    elif args.list_metrics:
        list_available_metrics(args.db)
    elif args.save:
        save_example_strategies(args.db)
    else:
        print_strategy_syntax()
        print("\n\nRun with --save to save strategies, --list-metrics to see available metrics")
