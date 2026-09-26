#!/usr/bin/env python
"""Quick test to verify Phase 0 DB initialization."""

from stockscreener.db import init_db

con = init_db()
cursor = con.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

print(f"✓ Database initialized with {len(tables)} tables")
print("Tables:", ", ".join(tables))

# Verify specific tables
expected = ["companies", "prices", "technicals_latest", "fundamentals", "fundamentals_latest",
            "custom_line_items", "strategies", "data_refresh_log"]
for table in expected:
    if table in tables:
        print(f"  ✓ {table}")
    else:
        print(f"  ✗ {table} MISSING")

con.close()
