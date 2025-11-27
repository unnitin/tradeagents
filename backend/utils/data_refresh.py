"""Data backfill and incremental update helpers for prices/features, news, and trades."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Optional, Sequence

from .constants import (
    DATA_DB_PATH,
    NEWS_DEFAULT_LOOKBACK_DAYS,
    PRICE_DEFAULT_FEATURES,
    TRADES_DEFAULT_LOOKBACK_DAYS,
)
from . import db
from ..data_provider import (
    MarketDataProvider,
    NewsDataProvider,
    PriceCandle,
    TradeDataProvider,
    YahooMarketDataProvider,
)


def run_setup(db_path: str) -> None:
    """Drop and recreate the prices/features tables in the SQLite database.

    Args:
        db_path: Filesystem path to the SQLite cache to reset.
    """
    with db.connect(db_path) as conn:
        db.drop_and_create_price_tables(conn)


def run_backfill_prices(
    provider: MarketDataProvider,
    symbols: Sequence[str],
    *,
    days: int,
    interval: str = "1d",
    feature_names: Optional[Iterable[str]] = None,
    db_path: str = DATA_DB_PATH,
) -> None:
    """Backfill a fixed window of OHLCV bars and recompute features.

    Args:
        provider: MarketDataProvider used to fetch OHLCV candles.
        symbols: Sequence of tickers to refresh.
        days: Lookback window size counted backwards from now.
        interval: Bar size such as '1d' or '1h'.
        feature_names: Optional list of feature IDs to recompute; defaults to PRICE_DEFAULT_FEATURES.
        db_path: SQLite database location for cached tables.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    with db.connect(db_path) as conn:
        db.drop_and_create_price_tables(conn)
        for symbol in symbols:
            candles = provider.get_price_series(symbol, start_date, end_date, interval=interval)
            db.upsert_prices(conn, symbol, interval, candles, replace_existing=True)
            db.recompute_features(conn, symbol, interval, feature_names or PRICE_DEFAULT_FEATURES)


def run_incremental_update_prices(
    provider: MarketDataProvider,
    symbols: Sequence[str],
    *,
    interval: str = "1d",
    feature_names: Optional[Iterable[str]] = None,
    db_path: str = DATA_DB_PATH,
    lookback_if_empty_days: int = 5,
) -> None:
    """Upsert new OHLCV rows and recompute features for provided symbols.

    Args:
        provider: MarketDataProvider used for incremental fetches.
        symbols: Sequence of tickers to refresh.
        interval: Bar size such as '1d'.
        feature_names: Optional features to recompute; defaults to PRICE_DEFAULT_FEATURES.
        db_path: SQLite database location for cached tables.
        lookback_if_empty_days: Days to backfill when cache is empty.
    """
    with db.connect(db_path) as conn:
        db.ensure_price_tables(conn)
        for symbol in symbols:
            start_ts = db.next_start_timestamp(conn, symbol, interval, lookback_if_empty_days)
            end_date = datetime.utcnow()
            candles = provider.get_price_series(symbol, start_ts, end_date, interval=interval)
            db.upsert_prices(conn, symbol, interval, candles, replace_existing=False)
            db.recompute_features(conn, symbol, interval, feature_names or PRICE_DEFAULT_FEATURES)


# Backwards-compat aliases
def run_backfill(
    *, provider: MarketDataProvider, symbols: Sequence[str], days: int, interval: str = "1d", feature_names: Optional[Iterable[str]] = None, db_path: str = DATA_DB_PATH
) -> None:
    """Compatibility wrapper for run_backfill_prices with identical arguments.

    Args:
        provider: Market data provider instance.
        symbols: Sequence of tickers to refresh.
        days: Lookback window in days.
        interval: Bar size string.
        feature_names: Optional feature names to recompute.
        db_path: SQLite database location.
    """
    run_backfill_prices(provider=provider, symbols=symbols, days=days, interval=interval, feature_names=feature_names, db_path=db_path)


def run_incremental_update(
    *,
    provider: MarketDataProvider,
    symbols: Sequence[str],
    interval: str = "1d",
    feature_names: Optional[Iterable[str]] = None,
    db_path: str = DATA_DB_PATH,
    lookback_if_empty_days: int = 5,
) -> None:
    """Compatibility wrapper for run_incremental_update_prices with identical arguments.

    Args:
        provider: Market data provider instance.
        symbols: Sequence of tickers to refresh.
        interval: Bar size string.
        feature_names: Optional feature names to recompute.
        db_path: SQLite database location.
        lookback_if_empty_days: Lookback window when cache is empty.
    """
    run_incremental_update_prices(provider=provider, symbols=symbols, interval=interval, feature_names=feature_names, db_path=db_path, lookback_if_empty_days=lookback_if_empty_days)


def run_backfill_news(
    symbols: Sequence[str],
    days: int = NEWS_DEFAULT_LOOKBACK_DAYS,
    db_path: str = DATA_DB_PATH,
    news_provider: NewsDataProvider = None,  # type: ignore[assignment]
) -> None:
    """Backfill news articles for symbols by dropping and recreating the news table.

    Args:
        symbols: Sequence of tickers to refresh.
        days: Lookback period in days to capture.
        db_path: SQLite database location that stores the news table.
        news_provider: Provider implementation used to fetch articles.

    Raises:
        ValueError: If a news_provider is not supplied.
    """
    if news_provider is None:
        raise ValueError("news_provider is required")

    start_date = datetime.utcnow().date() - timedelta(days=days)
    end_date = datetime.utcnow().date()

    with db.connect(db_path) as conn:
        db.drop_and_create_news_table(conn)
        for symbol in symbols:
            articles = news_provider.get_news(symbol, start_date, end_date)
            db.upsert_news(conn, symbol, articles, replace_existing=True)


def run_incremental_update_news(
    symbols: Sequence[str],
    db_path: str = DATA_DB_PATH,
    news_provider: NewsDataProvider = None,  # type: ignore[assignment]
    lookback_if_empty_days: int = NEWS_DEFAULT_LOOKBACK_DAYS,
) -> None:
    """Upsert news articles; uses recent lookback if table is empty.

    Args:
        symbols: Sequence of tickers to refresh.
        db_path: SQLite database location that stores the news table.
        news_provider: Provider implementation used to fetch articles.
        lookback_if_empty_days: Lookback to seed the table if no rows exist.

    Raises:
        ValueError: If a news_provider is not supplied.
    """
    if news_provider is None:
        raise ValueError("news_provider is required")

    with db.connect(db_path) as conn:
        db.ensure_news_table(conn)
        for symbol in symbols:
            start_date = db.next_news_start_date(conn, symbol, lookback_if_empty_days)
            end_date = datetime.utcnow().date()
            articles = news_provider.get_news(symbol, start_date, end_date)
            db.upsert_news(conn, symbol, articles, replace_existing=False)


def run_backfill_trades(
    symbols: Sequence[str],
    days: int,
    db_path: str = DATA_DB_PATH,
    trade_provider: TradeDataProvider = None,  # type: ignore[assignment]
) -> None:
    """Backfill trade disclosures by dropping and recreating the trades table.

    Args:
        symbols: Sequence of tickers to refresh.
        days: Lookback period in days to fetch.
        db_path: SQLite database location for the trades table.
        trade_provider: Provider implementation used to fetch trade records.

    Raises:
        ValueError: If trade_provider is not supplied.
    """
    if trade_provider is None:
        raise ValueError("trade_provider is required")

    start_date = datetime.utcnow().date() - timedelta(days=days)
    end_date = datetime.utcnow().date()

    with db.connect(db_path) as conn:
        db.drop_and_create_trades_table(conn)
        for symbol in symbols:
            trades = trade_provider.get_trades(symbol, start_date, end_date)
            db.upsert_trades(conn, symbol, trades, replace_existing=True)


def run_incremental_update_trades(
    symbols: Sequence[str],
    db_path: str = DATA_DB_PATH,
    trade_provider: TradeDataProvider = None,  # type: ignore[assignment]
    lookback_if_empty_days: int = TRADES_DEFAULT_LOOKBACK_DAYS,
) -> None:
    """Upsert new trade disclosures; seeds with lookback if empty.

    Args:
        symbols: Sequence of tickers to refresh.
        db_path: SQLite database location for the trades table.
        trade_provider: Provider implementation used to fetch trade records.
        lookback_if_empty_days: Lookback window if the cache lacks data.

    Raises:
        ValueError: If trade_provider is not supplied.
    """
    if trade_provider is None:
        raise ValueError("trade_provider is required")

    with db.connect(db_path) as conn:
        db.ensure_trades_table(conn)
        for symbol in symbols:
            start_date = db.next_trades_start_date(conn, symbol, lookback_if_empty_days)
            end_date = datetime.utcnow().date()
            trades = trade_provider.get_trades(symbol, start_date, end_date)
            db.upsert_trades(conn, symbol, trades, replace_existing=False)
