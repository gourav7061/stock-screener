#!/usr/bin/env python
"""Refresh India fundamentals from Screener.in."""

import sys
import argparse
import sqlite3
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

from stockscreener.db import get_connection, log_refresh, update_refresh_log
from stockscreener.screener_in import refresh_india_fundamentals as _refresh
from stockscreener.config import DB_PATH


def refresh_india_fundamentals(con: sqlite3.Connection, tickers: List[str] = None,
                                progress_callback=None) -> dict:
    """Refresh India fundamentals for all India tickers (or a subset) via Screener.in.

    Args:
        con: Database connection
        tickers: List of tickers to refresh (default: all India tickers with has_fundamentals=1)
        progress_callback: Optional callback(current, total, status) for progress

    Returns:
        Dict with stats
    """
    log_id = log_refresh(con, "india_fundamentals", market="IN", status="running")

    try:
        cursor = con.cursor()
        if tickers:
            placeholders = ",".join(["?" for _ in tickers])
            cursor.execute(f"SELECT ticker FROM companies WHERE market = 'IN' AND ticker IN ({placeholders})",
                          tickers)
        else:
            cursor.execute("SELECT ticker FROM companies WHERE market = 'IN' AND has_fundamentals = 1")

        in_tickers = [row[0] for row in cursor.fetchall()]
        stats = _refresh(con, in_tickers, progress_callback=progress_callback)

        status = "success" if stats["failed"] == 0 else "partial" if stats["succeeded"] else "failed"
        update_refresh_log(con, log_id, status, tickers_attempted=stats["attempted"],
                          tickers_succeeded=stats["succeeded"], tickers_failed=stats["failed"],
                          failed_tickers=stats["failed_tickers"])

        return stats

    except Exception as e:
        update_refresh_log(con, log_id, "failed", error_summary=str(e))
        raise


def main():
    parser = argparse.ArgumentParser(description="Refresh India fundamentals from Screener.in")
    parser.add_argument("--tickers", nargs="+", help="Specific tickers to refresh (e.g. RELIANCE.NS)")

    args = parser.parse_args()

    con = get_connection(DB_PATH)

    try:
        stats = refresh_india_fundamentals(con, tickers=args.tickers)
        print(f"\n✓ India Fundamentals refresh complete")
        print(f"  Attempted: {stats['attempted']}, Succeeded: {stats['succeeded']}, Failed: {stats['failed']}")
        if stats["failed_tickers"]:
            print(f"  Failed tickers: {', '.join(stats['failed_tickers'])}")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        con.close()


if __name__ == "__main__":
    main()
