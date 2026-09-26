#!/usr/bin/env python
"""Refresh price data and recompute technicals."""

import sys
import argparse
import sqlite3
from datetime import datetime, timezone

sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))

from stockscreener.db import get_connection, log_refresh, update_refresh_log
from stockscreener.yfinance_client import fetch_prices_batch, get_last_stored_date
from stockscreener.technicals import compute_and_store_technicals
from stockscreener.config import DB_PATH, PRICE_BATCH_SIZE, PRICE_BATCH_SLEEP_SECONDS
import time


def refresh_prices(con: sqlite3.Connection, market: str = "US", tickers: list = None,
                  period: str = "2y", progress_callback=None):
    """Refresh price data for tickers.

    Args:
        con: Database connection
        market: 'US', 'IN', or 'ALL'
        tickers: List of specific tickers, or None for all in market
        period: Historical period to fetch (e.g., '1y', '2y', '5y')
        progress_callback: Optional callback(current, total, status)

    Returns:
        Stats dict
    """
    import pandas as pd

    log_id = log_refresh(con, "prices", market=market, status="running")

    try:
        # Get tickers for this market
        cursor = con.cursor()
        if tickers:
            placeholders = ",".join(["?" for _ in tickers])
            cursor.execute(f"SELECT ticker FROM companies WHERE ticker IN ({placeholders})", tickers)
        elif market == "ALL":
            cursor.execute("SELECT ticker FROM companies WHERE is_active = 1")
        else:
            cursor.execute("SELECT ticker FROM companies WHERE market = ? AND is_active = 1", (market,))

        all_tickers = [row[0] for row in cursor.fetchall()]
        total = len(all_tickers)
        succeeded = 0
        failed = 0
        failed_list = []

        print(f"Refreshing prices for {total} tickers ({market})...")

        # Process in batches
        for batch_start in range(0, len(all_tickers), PRICE_BATCH_SIZE):
            batch = all_tickers[batch_start:batch_start + PRICE_BATCH_SIZE]

            if progress_callback:
                progress_callback(batch_start + 1, total, f"Fetching batch {batch_start // PRICE_BATCH_SIZE + 1}...")

            try:
                # Fetch price data
                price_data = fetch_prices_batch(batch, period=period)

                # Store prices and compute technicals
                for ticker, df in price_data.items():
                    if df.empty:
                        failed += 1
                        failed_list.append(ticker)
                        continue

                    try:
                        # Insert prices
                        for date, row in df.iterrows():
                            cursor.execute("""
                                INSERT OR REPLACE INTO prices
                                (ticker, date, open, high, low, close, adj_close, volume)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (ticker, date.strftime("%Y-%m-%d"), row.get("Open"), row.get("High"),
                                 row.get("Low"), row.get("Close"), row.get("Adj Close"), int(row.get("Volume", 0))))

                        con.commit()

                        # Compute technicals
                        compute_and_store_technicals(con, ticker)
                        succeeded += 1

                    except Exception as e:
                        print(f"  Error processing {ticker}: {e}")
                        failed += 1
                        failed_list.append(ticker)

                # Throttle between batches
                if batch_start + PRICE_BATCH_SIZE < len(all_tickers):
                    time.sleep(PRICE_BATCH_SLEEP_SECONDS)

            except Exception as e:
                print(f"  Batch fetch error: {e}")
                failed += len(batch)
                failed_list.extend(batch)

        # Update log
        update_refresh_log(con, log_id, "success" if failed == 0 else "partial",
                          tickers_attempted=total, tickers_succeeded=succeeded,
                          tickers_failed=failed, failed_tickers=failed_list)

        return {"attempted": total, "succeeded": succeeded, "failed": failed}

    except Exception as e:
        update_refresh_log(con, log_id, "failed", error_summary=str(e))
        raise


def main():
    parser = argparse.ArgumentParser(description="Refresh price data and technicals")
    parser.add_argument("--market", choices=["US", "IN", "ALL"], default="US",
                       help="Market to refresh")
    parser.add_argument("--tickers", nargs="+", help="Specific tickers to refresh")
    parser.add_argument("--period", default="2y", help="Historical period (default: 2y)")

    args = parser.parse_args()

    con = get_connection(DB_PATH)

    try:
        stats = refresh_prices(con, market=args.market, tickers=args.tickers, period=args.period)
        print(f"\n✓ Price refresh complete")
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
    from stockscreener.db import get_connection
    main()
