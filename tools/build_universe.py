#!/usr/bin/env python
"""Build/refresh the companies table with US and India ticker universe."""

import sys
import argparse
from datetime import datetime, timezone
import sqlite3

# Add parent to path so we can import stockscreener
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))

from stockscreener.db import init_db, get_connection, upsert, log_refresh, update_refresh_log
from stockscreener.us_tickers import build_us_universe
from stockscreener.india_tickers import build_india_universe
from stockscreener.config import DB_PATH


def populate_companies(con: sqlite3.Connection, market: str = "US", test_mode: bool = True):
    """Fetch and populate the companies table for a given market.

    Args:
        con: Database connection
        market: "US" or "IN"
        test_mode: If True, use small test set (S&P 100, Nifty 50)
    """
    # Start logging
    log_id = log_refresh(con, "universe", market=market, status="running")

    try:
        if market == "US":
            print(f"Fetching {'S&P 100 (test)' if test_mode else 'full US'} universe...")
            df = build_us_universe(test_mode=test_mode)
        elif market == "IN":
            print(f"Fetching {'Nifty 50 (test)' if test_mode else 'full India'} universe...")
            df = build_india_universe(test_mode=test_mode)
        else:
            raise ValueError(f"Unknown market: {market}")

        print(f"  → Fetched {len(df)} tickers")

        # Add standard columns
        now = datetime.now(timezone.utc).isoformat()
        df["has_fundamentals"] = 0
        df["is_active"] = 1
        df["last_seen_at"] = now
        df["created_at"] = now
        df["updated_at"] = now

        # For US: set has_fundamentals=1 for all (full SEC EDGAR coverage)
        # For India: set has_fundamentals=1 only for Nifty500/BSE500 (tiered approach)
        if market == "US":
            df["has_fundamentals"] = 1
        elif market == "IN":
            df["has_fundamentals"] = df["index_membership"].notna().astype(int)

        # Convert to records for upsert
        rows = df.to_dict('records')

        # Upsert into companies table
        cursor = con.cursor()
        affected = 0
        for row in rows:
            # Remove NaN values
            row = {k: v for k, v in row.items() if pd.notna(v)}

            cursor.execute("""
                INSERT OR REPLACE INTO companies
                (ticker, exchange, market, name, cik, index_membership, has_fundamentals, is_active, last_seen_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row.get("ticker"),
                row.get("exchange"),
                row.get("market"),
                row.get("name"),
                row.get("cik"),
                row.get("index_membership"),
                row.get("has_fundamentals"),
                row.get("is_active"),
                row.get("last_seen_at"),
                row.get("created_at"),
                row.get("updated_at"),
            ))
            affected += 1

        con.commit()

        # Verify
        cursor.execute("SELECT COUNT(*) FROM companies WHERE market = ?", (market,))
        total_count = cursor.fetchone()[0]

        print(f"  → Inserted/updated {affected} rows")
        print(f"  → Total {market} companies now in DB: {total_count}")

        # Log success
        update_refresh_log(con, log_id, "success", tickers_attempted=len(df),
                          tickers_succeeded=len(df), tickers_failed=0,
                          error_summary=None)

        return True

    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)}"
        traceback.print_exc()

        # Log failure
        update_refresh_log(con, log_id, "failed", tickers_attempted=0,
                          tickers_succeeded=0, tickers_failed=0,
                          error_summary=error_msg)

        return False


def main():
    parser = argparse.ArgumentParser(description="Build/refresh the companies universe")
    parser.add_argument("--market", choices=["US", "IN", "ALL"], default="ALL",
                       help="Market to build (US, IN, or both)")
    parser.add_argument("--full", action="store_true",
                       help="Fetch full universe instead of test set (S&P 100, Nifty 50)")

    args = parser.parse_args()
    test_mode = not args.full

    # Initialize DB if needed
    init_db(DB_PATH)
    con = get_connection(DB_PATH)

    success = True
    if args.market in ("US", "ALL"):
        print("\n=== Building US Universe ===")
        if not populate_companies(con, "US", test_mode=test_mode):
            success = False

    if args.market in ("IN", "ALL"):
        print("\n=== Building India Universe ===")
        if not populate_companies(con, "IN", test_mode=test_mode):
            success = False

    con.close()

    if success:
        print("\n✓ Universe build completed successfully")
        sys.exit(0)
    else:
        print("\n✗ Universe build encountered errors")
        sys.exit(1)


if __name__ == "__main__":
    import pandas as pd  # Import here to avoid import-order issues
    main()
