#!/usr/bin/env python
"""Verify Phase 1: Universe population."""

from stockscreener.db import get_connection
from stockscreener.config import DB_PATH

con = get_connection(DB_PATH)
cursor = con.cursor()

# Row counts
cursor.execute("SELECT COUNT(*) FROM companies")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM companies WHERE market = 'US'")
us_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM companies WHERE market = 'IN'")
in_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM companies WHERE has_fundamentals = 1")
has_fund = cursor.fetchone()[0]

# Spot checks
cursor.execute("SELECT ticker, exchange, name FROM companies WHERE ticker = 'AAPL'")
aapl = cursor.fetchone()

cursor.execute("SELECT ticker, exchange, name FROM companies WHERE ticker = 'RELIANCE.NS'")
reliance = cursor.fetchone()

print(f"✓ Phase 1 Verification")
print(f"  Total tickers: {total}")
print(f"  US tickers: {us_count}")
print(f"  India tickers: {in_count}")
print(f"  With fundamentals: {has_fund}")
print(f"\nSpot Checks:")
print(f"  AAPL: {dict(aapl) if aapl else 'NOT FOUND'}")
print(f"  RELIANCE.NS: {dict(reliance) if reliance else 'NOT FOUND'}")

# Verify data integrity
assert total == 89, f"Expected 89 tickers, got {total}"
assert us_count == 40, f"Expected 40 US tickers, got {us_count}"
assert in_count == 49, f"Expected 49 India tickers, got {in_count}"
assert has_fund >= 89, f"All tickers should have_fundamentals=1, got {has_fund}"
assert aapl is not None, "AAPL not found"
assert reliance is not None, "RELIANCE.NS not found"

print(f"\n✓ All checks passed!")

con.close()
