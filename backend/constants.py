"""Shared constants for backend service."""

DATE_FORMAT = "%Y-%m-%d"
DATA_DB_PATH = "data.db"

# Default feature set computed for price backfills/updates.
PRICE_DEFAULT_FEATURES = ["return_pct", "sma_5", "ema_10", "volatility_5"]

# Default lookbacks for cached data domains.
NEWS_DEFAULT_LOOKBACK_DAYS = 30
TRADES_DEFAULT_LOOKBACK_DAYS = 30
