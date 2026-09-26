"""Configuration and constants for the stock screener."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "stock_screener.db"

# Ensure data directory exists
DB_PATH.parent.mkdir(exist_ok=True)

# SEC EDGAR configuration
SEC_EDGAR_USER_AGENT = os.environ.get("SEC_EDGAR_USER_AGENT", "StockScreenerDashboard (gourav.modi7061@gmail.com)")
SEC_EDGAR_BASE_URL = "https://data.sec.gov/api/xbrl"
SEC_EDGAR_RATE_LIMIT = 10  # requests per second

# Price fetching configuration
PRICE_BATCH_SIZE = 75
PRICE_BATCH_SLEEP_SECONDS = 2.0

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = (5, 15, 45)

# Screener.in configuration
SCREENER_IN_REQUEST_DELAY_SECONDS = 2.0
SCREENER_IN_BASE_URL = "https://www.screener.in"

# Data staleness warning threshold (days)
STALENESS_WARNING_DAYS = 7
