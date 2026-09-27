"""Database initialization and helper functions."""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import json

from .config import DB_PATH


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Initialize the database by running the schema. Idempotent."""
    schema_path = Path(__file__).parent / "schema.sql"

    con = sqlite3.connect(str(db_path), timeout=30)
    with open(schema_path, "r") as f:
        con.executescript(f.read())
    con.commit()

    _migrate_missing_columns(con)
    con.commit()
    con.close()

    return get_connection(db_path)


def _migrate_missing_columns(con: sqlite3.Connection) -> None:
    """Add columns to tables that exist in the schema but not in an older table on disk
    (CREATE TABLE IF NOT EXISTS skips existing tables, so new columns never land there
    without this)."""
    tables_and_columns = {
        "technicals_latest": {
            "sma150": "REAL", "sma220": "REAL", "ema220": "REAL",
            '"52w_low"': "REAL", '"52w_low_25pct"': "REAL", '"52w_high"': "REAL",
        },
        "fundamentals_latest": {
            "current_price": "REAL", "high_52w": "REAL", "low_52w": "REAL",
            "book_value": "REAL", "roce": "REAL", "face_value": "REAL",
            "debt": "REAL", "net_worth": "REAL", "source": "TEXT",
        },
    }

    cursor = con.cursor()
    for table, expected_columns in tables_and_columns.items():
        cursor.execute(f"PRAGMA table_info({table})")
        existing = {row[1] for row in cursor.fetchall()}

        for col, col_type in expected_columns.items():
            col_name = col.strip('"')
            if col_name not in existing:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Get a connection to the database."""
    con = sqlite3.connect(str(db_path), timeout=30)
    con.row_factory = sqlite3.Row
    # Streamlit Cloud can have multiple sessions hitting this file concurrently;
    # WAL lets reads and writes overlap instead of raising "database is locked".
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    return con


def upsert(con: sqlite3.Connection, table: str, rows: list[dict], conflict_keys: list[str]) -> int:
    """Generic INSERT ... ON CONFLICT DO UPDATE for a list of dictionaries.

    Args:
        con: Database connection
        table: Table name
        rows: List of dicts to insert/update
        conflict_keys: Column names that form the conflict key (usually PRIMARY KEY or UNIQUE columns)

    Returns:
        Number of rows affected
    """
    if not rows:
        return 0

    # Get columns from first row
    columns = list(rows[0].keys())

    # Build the SQL statement
    placeholders = ", ".join(["?" for _ in columns])
    col_names = ", ".join(columns)
    set_clause = ", ".join([f"{col} = excluded.{col}" for col in columns if col not in conflict_keys])

    sql = f"""
    INSERT OR REPLACE INTO {table} ({col_names})
    VALUES ({placeholders})
    """

    # Prepare data for insertion
    values_list = [tuple(row.get(col) for col in columns) for row in rows]

    cursor = con.cursor()
    cursor.executemany(sql, values_list)
    con.commit()

    return cursor.rowcount


def log_refresh(con: sqlite3.Connection, data_type: str, market: str = None, status: str = "running",
                tickers_attempted: int = None, tickers_succeeded: int = None, tickers_failed: int = None,
                failed_tickers: list = None, error_summary: str = None, notes: str = None) -> int:
    """Log a data refresh operation."""
    now = datetime.now(timezone.utc).isoformat()
    failed_tickers_json = json.dumps(failed_tickers) if failed_tickers else None

    cursor = con.cursor()
    cursor.execute("""
        INSERT INTO data_refresh_log (data_type, market, started_at, finished_at, status,
                                      tickers_attempted, tickers_succeeded, tickers_failed,
                                      failed_tickers_json, error_summary, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data_type, market, now, None if status == "running" else now,
          status, tickers_attempted, tickers_succeeded, tickers_failed, failed_tickers_json, error_summary, notes))

    con.commit()
    return cursor.lastrowid


def update_refresh_log(con: sqlite3.Connection, log_id: int, status: str, tickers_attempted: int = None,
                       tickers_succeeded: int = None, tickers_failed: int = None,
                       failed_tickers: list = None, error_summary: str = None) -> None:
    """Update a data refresh log entry."""
    now = datetime.now(timezone.utc).isoformat()
    failed_tickers_json = json.dumps(failed_tickers) if failed_tickers else None

    cursor = con.cursor()
    cursor.execute("""
        UPDATE data_refresh_log
        SET status = ?, finished_at = ?, tickers_attempted = ?,
            tickers_succeeded = ?, tickers_failed = ?, failed_tickers_json = ?,
            error_summary = ?
        WHERE id = ?
    """, (status, now, tickers_attempted, tickers_succeeded,
          tickers_failed, failed_tickers_json, error_summary, log_id))

    con.commit()


def get_last_refresh(con: sqlite3.Connection, data_type: str, market: str = None) -> dict or None:
    """Get the last successful refresh log entry."""
    cursor = con.cursor()
    if market:
        cursor.execute("""
            SELECT * FROM data_refresh_log
            WHERE data_type = ? AND market = ? AND status = 'success'
            ORDER BY finished_at DESC LIMIT 1
        """, (data_type, market))
    else:
        cursor.execute("""
            SELECT * FROM data_refresh_log
            WHERE data_type = ? AND status = 'success'
            ORDER BY finished_at DESC LIMIT 1
        """, (data_type,))

    row = cursor.fetchone()
    return dict(row) if row else None
