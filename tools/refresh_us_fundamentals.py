#!/usr/bin/env python
"""Refresh US fundamentals from SEC EDGAR."""

import sys
import argparse
import sqlite3
from datetime import datetime, timezone
import os

sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))

from stockscreener.db import get_connection, log_refresh, update_refresh_log
from stockscreener.sec_edgar import fetch_companyfacts, normalize_companyfacts, US_GAAP_MAP
from stockscreener.config import DB_PATH, SEC_EDGAR_USER_AGENT


def refresh_us_fundamentals(con: sqlite3.Connection, tickers: List[str] = None, progress_callback=None):
    """Refresh US fundamentals for all US tickers (or a subset).

    Args:
        con: Database connection
        tickers: List of tickers to refresh (default: all US)
        progress_callback: Optional callback(current, total, status) for progress

    Returns:
        Dict with stats
    """
    from typing import List

    log_id = log_refresh(con, "us_fundamentals", market="US", status="running")

    try:
        # Get US tickers with fundamentals
        cursor = con.cursor()
        if tickers:
            placeholders = ",".join(["?" for _ in tickers])
            cursor.execute(f"SELECT ticker, cik FROM companies WHERE market = 'US' AND ticker IN ({placeholders})",
                          tickers)
        else:
            cursor.execute("SELECT ticker, cik FROM companies WHERE market = 'US' AND cik IS NOT NULL")

        us_tickers = [(row[0], row[1]) for row in cursor.fetchall()]
        total = len(us_tickers)
        succeeded = 0
        failed = 0
        failed_list = []

        print(f"Refreshing US fundamentals for {total} tickers...")

        for idx, (ticker, cik) in enumerate(us_tickers):
            if progress_callback:
                progress_callback(idx + 1, total, f"Fetching {ticker}...")

            try:
                # Fetch from SEC
                facts = fetch_companyfacts(cik, SEC_EDGAR_USER_AGENT)

                if not facts:
                    failed += 1
                    failed_list.append(ticker)
                    continue

                # Normalize
                rows = normalize_companyfacts(cik, ticker, facts, US_GAAP_MAP)

                # Insert/update
                for row in rows:
                    cursor.execute("""
                        INSERT OR REPLACE INTO fundamentals
                        (ticker, fiscal_period, period_end_date, line_item_key, line_item_label,
                         value, unit, source, is_custom, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (row["ticker"], row["fiscal_period"], row["period_end_date"],
                          row["line_item_key"], row["line_item_label"], row["value"],
                          row["unit"], row["source"], row["is_custom"], row["fetched_at"]))

                con.commit()
                succeeded += 1

            except Exception as e:
                logger.debug(f"Error processing {ticker}: {e}")
                failed += 1
                failed_list.append(ticker)

        # Update log
        update_refresh_log(con, log_id, "success" if failed == 0 else "partial",
                          tickers_attempted=total, tickers_succeeded=succeeded,
                          tickers_failed=failed, failed_tickers=failed_list)

        return {"attempted": total, "succeeded": succeeded, "failed": failed}

    except Exception as e:
        update_refresh_log(con, log_id, "failed", error_summary=str(e))
        raise


def main():
    parser = argparse.ArgumentParser(description="Refresh US fundamentals from SEC EDGAR")
    parser.add_argument("--tickers", nargs="+", help="Specific tickers to refresh")

    args = parser.parse_args()

    con = get_connection(DB_PATH)

    try:
        stats = refresh_us_fundamentals(con, tickers=args.tickers)
        print(f"\n✓ US Fundamentals refresh complete")
        print(f"  Attempted: {stats['attempted']}, Succeeded: {stats['succeeded']}, Failed: {stats['failed']}")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        con.close()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    main()
