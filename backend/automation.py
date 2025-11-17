"""Automation utilities for backfilling and updating market data and features.

This module supports:
- One-time schema setup for the local SQLite store.
- Bulk backfill of OHLCV data for symbols over an interval and feature computation.
- Incremental upsert jobs to keep data and features fresh on a schedule.

Tables
-------
prices(symbol TEXT, ts TEXT, interval TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER)
features(symbol TEXT, ts TEXT, interval TEXT, feature_name TEXT, value REAL)

Both tables use PRIMARY KEY constraints to make inserts idempotent and safe for upserts.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
import sqlite3
from typing import Iterable, List, Optional, Sequence

from .constants import (
    DATA_DB_PATH,
    NEWS_DEFAULT_LOOKBACK_DAYS,
    PRICE_DEFAULT_FEATURES,
    TRADES_DEFAULT_LOOKBACK_DAYS,
)
from .data_provider import (
    MarketDataProvider,
    NewsArticle,
    NewsDataProvider,
    PriceCandle,
    TradeDataProvider,
    TradeRecord,
    YahooMarketDataProvider,
)
from .feature_engineering import compute_features


def run_setup(db_path: str) -> None:
    """Drop and recreate the prices/features tables in the SQLite database."""
    with _connect(db_path) as conn:
        _drop_and_create_price_tables(conn)

def run_backfill_prices(
    provider: MarketDataProvider,
    symbols: Sequence[str],
    *,
    days: int,
    interval: str = "1d",
    feature_names: Optional[Iterable[str]] = None,
    db_path: str = DATA_DB_PATH,
) -> None:
    """Backfill <<days>> of OHLCV for symbols, recomputing features from scratch.

    Drops and recreates price/feature tables, then inserts data from the given provider.
    Pass `YahooMarketDataProvider()` for default live data, or inject another provider
    for tests/offline use.
    """

    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    with _connect(db_path) as conn:
        _drop_and_create_price_tables(conn)
        for symbol in symbols:
            candles = provider.get_price_series(symbol, start_date, end_date, interval=interval)
            _upsert_prices(conn, symbol, interval, candles, replace_existing=True)
            _recompute_features(conn, symbol, interval, feature_names or PRICE_DEFAULT_FEATURES)


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

    Intended to run on a schedule (e.g., every 5 or 15 minutes). If no data
    exists yet, it seeds using the given lookback window instead of dropping tables.
    Pass `YahooMarketDataProvider()` for default live data, or inject another provider
    for tests/offline use.
    """

    with _connect(db_path) as conn:
        _ensure_price_tables(conn)
        for symbol in symbols:
            start_ts = _next_start_timestamp(conn, symbol, interval, lookback_if_empty_days)
            end_date = datetime.utcnow()
            candles = provider.get_price_series(symbol, start_ts, end_date, interval=interval)
            _upsert_prices(conn, symbol, interval, candles, replace_existing=False)
            _recompute_features(conn, symbol, interval, feature_names or PRICE_DEFAULT_FEATURES)

# Backwards-compat aliases
def run_backfill(*, provider: MarketDataProvider, symbols: Sequence[str], days: int, interval: str = "1d", feature_names: Optional[Iterable[str]] = None, db_path: str = DATA_DB_PATH) -> None:
    run_backfill_prices(provider=provider, symbols=symbols, days=days, interval=interval, feature_names=feature_names, db_path=db_path)


def run_incremental_update(*, provider: MarketDataProvider, symbols: Sequence[str], interval: str = "1d", feature_names: Optional[Iterable[str]] = None, db_path: str = DATA_DB_PATH, lookback_if_empty_days: int = 5) -> None:
    run_incremental_update_prices(provider=provider, symbols=symbols, interval=interval, feature_names=feature_names, db_path=db_path, lookback_if_empty_days=lookback_if_empty_days)


def run_backfill_news(
    symbols: Sequence[str],
    days: int = NEWS_DEFAULT_LOOKBACK_DAYS,
    db_path: str = DATA_DB_PATH,
    news_provider: NewsDataProvider = None,  # type: ignore[assignment]
) -> None:
    """Backfill news articles for symbols by dropping and recreating the news table."""

    if news_provider is None:
        raise ValueError("news_provider is required")

    start_date = datetime.utcnow().date() - timedelta(days=days)
    end_date = datetime.utcnow().date()

    with _connect(db_path) as conn:
        _drop_and_create_news_table(conn)
        for symbol in symbols:
            articles = news_provider.get_news(symbol, start_date, end_date)
            _upsert_news(conn, symbol, articles, replace_existing=True)


def run_incremental_update_news(
    symbols: Sequence[str],
    db_path: str = DATA_DB_PATH,
    news_provider: NewsDataProvider = None,  # type: ignore[assignment]
    lookback_if_empty_days: int = NEWS_DEFAULT_LOOKBACK_DAYS,
) -> None:
    """Upsert news articles; uses recent lookback if table is empty."""

    if news_provider is None:
        raise ValueError("news_provider is required")

    with _connect(db_path) as conn:
        _ensure_news_table(conn)
        for symbol in symbols:
            start_date = _next_news_start_date(conn, symbol, lookback_if_empty_days)
            end_date = datetime.utcnow().date()
            articles = news_provider.get_news(symbol, start_date, end_date)
            _upsert_news(conn, symbol, articles, replace_existing=False)


def run_backfill_trades(
    symbols: Sequence[str],
    days: int,
    db_path: str = DATA_DB_PATH,
    trade_provider: TradeDataProvider = None,  # type: ignore[assignment]
) -> None:
    """Backfill trade disclosures (e.g., politician trades) by dropping and recreating the trades table."""

    if trade_provider is None:
        raise ValueError("trade_provider is required")

    start_date = datetime.utcnow().date() - timedelta(days=days)
    end_date = datetime.utcnow().date()

    with _connect(db_path) as conn:
        _drop_and_create_trades_table(conn)
        for symbol in symbols:
            trades = trade_provider.get_trades(symbol, start_date, end_date)
            _upsert_trades(conn, symbol, trades, replace_existing=True)


def run_incremental_update_trades(
    symbols: Sequence[str],
    db_path: str = DATA_DB_PATH,
    trade_provider: TradeDataProvider = None,  # type: ignore[assignment]
    lookback_if_empty_days: int = TRADES_DEFAULT_LOOKBACK_DAYS,
) -> None:
    """Upsert new trade disclosures; seeds with lookback if empty."""

    if trade_provider is None:
        raise ValueError("trade_provider is required")

    with _connect(db_path) as conn:
        _ensure_trades_table(conn)
        for symbol in symbols:
            start_date = _next_trades_start_date(conn, symbol, lookback_if_empty_days)
            end_date = datetime.utcnow().date()
            trades = trade_provider.get_trades(symbol, start_date, end_date)
            _upsert_trades(conn, symbol, trades, replace_existing=False)


# --- Internal helpers -----------------------------------------------------

def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def _drop_and_create_price_tables(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS prices;")
    conn.execute("DROP TABLE IF EXISTS features;")
    conn.execute(
        """
        CREATE TABLE prices (
            symbol TEXT NOT NULL,
            ts TEXT NOT NULL,
            interval TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            PRIMARY KEY (symbol, ts, interval)
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE features (
            symbol TEXT NOT NULL,
            ts TEXT NOT NULL,
            interval TEXT NOT NULL,
            feature_name TEXT NOT NULL,
            value REAL,
            PRIMARY KEY (symbol, ts, interval, feature_name)
        );
        """
    )
    conn.commit()


def _ensure_price_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prices (
            symbol TEXT NOT NULL,
            ts TEXT NOT NULL,
            interval TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            PRIMARY KEY (symbol, ts, interval)
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS features (
            symbol TEXT NOT NULL,
            ts TEXT NOT NULL,
            interval TEXT NOT NULL,
            feature_name TEXT NOT NULL,
            value REAL,
            PRIMARY KEY (symbol, ts, interval, feature_name)
        );
        """
    )
    conn.commit()


def _drop_and_create_news_table(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS news;")
    conn.execute(
        """
        CREATE TABLE news (
            symbol TEXT NOT NULL,
            published_at TEXT NOT NULL,
            headline TEXT NOT NULL,
            summary TEXT,
            url TEXT,
            PRIMARY KEY (symbol, published_at, headline)
        );
        """
    )
    conn.commit()


def _ensure_news_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            symbol TEXT NOT NULL,
            published_at TEXT NOT NULL,
            headline TEXT NOT NULL,
            summary TEXT,
            url TEXT,
            PRIMARY KEY (symbol, published_at, headline)
        );
        """
    )
    conn.commit()


def _drop_and_create_trades_table(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS trades;")
    conn.execute(
        """
        CREATE TABLE trades (
            symbol TEXT NOT NULL,
            executed_at TEXT NOT NULL,
            trader TEXT NOT NULL,
            action TEXT NOT NULL,
            quantity REAL,
            price REAL,
            source TEXT,
            PRIMARY KEY (symbol, executed_at, trader, action, price)
        );
        """
    )
    conn.commit()


def _ensure_trades_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trades (
            symbol TEXT NOT NULL,
            executed_at TEXT NOT NULL,
            trader TEXT NOT NULL,
            action TEXT NOT NULL,
            quantity REAL,
            price REAL,
            source TEXT,
            PRIMARY KEY (symbol, executed_at, trader, action, price)
        );
        """
    )
    conn.commit()


def _upsert_prices(
    conn: sqlite3.Connection,
    symbol: str,
    interval: str,
    candles: List[PriceCandle],
    replace_existing: bool,
) -> None:
    if not candles:
        return
    statement = (
        "INSERT OR REPLACE INTO prices (symbol, ts, interval, open, high, low, close, volume)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        if replace_existing
        else "INSERT OR IGNORE INTO prices (symbol, ts, interval, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )
    payload = [
        (
            symbol,
            candle.date.isoformat(),
            interval,
            candle.open,
            candle.high,
            candle.low,
            candle.close,
            candle.volume,
        )
        for candle in candles
    ]
    conn.executemany(statement, payload)
    conn.commit()


def _recompute_features(
    conn: sqlite3.Connection,
    symbol: str,
    interval: str,
    feature_names: Iterable[str],
) -> None:
    # Load all prices for the window/interval to ensure rolling metrics are consistent.
    candles = _load_candles(conn, symbol, interval)
    feature_list = list(feature_names)
    feature_rows = compute_features(candles, feature_list)

    conn.execute("DELETE FROM features WHERE symbol = ? AND interval = ?", (symbol, interval))
    feature_payload = []
    for row in feature_rows:
        ts = row["date"]
        for feature_name in feature_list:
            feature_payload.append((symbol, ts, interval, feature_name, row.get(feature_name)))

    if feature_payload:
        conn.executemany(
            "INSERT OR REPLACE INTO features (symbol, ts, interval, feature_name, value) VALUES (?, ?, ?, ?, ?)",
            feature_payload,
        )
        conn.commit()


def _load_candles(conn: sqlite3.Connection, symbol: str, interval: str) -> List[PriceCandle]:
    rows = conn.execute(
        "SELECT ts, open, high, low, close, volume FROM prices WHERE symbol = ? AND interval = ? ORDER BY ts ASC",
        (symbol, interval),
    ).fetchall()
    return [
        PriceCandle(
            date=datetime.fromisoformat(ts),
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume,
        )
        for ts, open_price, high_price, low_price, close_price, volume in rows
    ]


def _next_start_timestamp(
    conn: sqlite3.Connection,
    symbol: str,
    interval: str,
    lookback_if_empty_days: int,
) -> datetime:
    row = conn.execute(
        "SELECT MAX(ts) FROM prices WHERE symbol = ? AND interval = ?", (symbol, interval)
    ).fetchone()
    latest_ts = row[0]
    if latest_ts:
        start = datetime.fromisoformat(latest_ts) + _interval_delta(interval)
    else:
        start = datetime.combine(date.today() - timedelta(days=lookback_if_empty_days), datetime.min.time())
    return start


def _interval_delta(interval: str) -> timedelta:
    if interval.endswith("m"):
        return timedelta(minutes=int(interval.rstrip("m")))
    if interval.endswith("h"):
        return timedelta(hours=int(interval.rstrip("h")))
    if interval.endswith("d"):
        return timedelta(days=int(interval.rstrip("d")))
    raise ValueError(f"Unsupported interval '{interval}'")


def _upsert_news(
    conn: sqlite3.Connection,
    symbol: str,
    articles: Sequence[NewsArticle],
    replace_existing: bool,
) -> None:
    if not articles:
        return
    statement = (
        "INSERT OR REPLACE INTO news (symbol, published_at, headline, summary, url) VALUES (?, ?, ?, ?, ?)"
        if replace_existing
        else "INSERT OR IGNORE INTO news (symbol, published_at, headline, summary, url) VALUES (?, ?, ?, ?, ?)"
    )
    payload = [
        (
            symbol,
            article.published_at.isoformat(),
            article.headline,
            article.summary,
            article.url,
        )
        for article in articles
    ]
    conn.executemany(statement, payload)
    conn.commit()


def _next_news_start_date(conn: sqlite3.Connection, symbol: str, lookback_if_empty_days: int) -> date:
    row = conn.execute("SELECT MAX(published_at) FROM news WHERE symbol = ?", (symbol,)).fetchone()
    latest_ts = row[0]
    if latest_ts:
        return datetime.fromisoformat(latest_ts).date()
    return date.today() - timedelta(days=lookback_if_empty_days)


def _upsert_trades(
    conn: sqlite3.Connection,
    symbol: str,
    trades: Sequence[TradeRecord],
    replace_existing: bool,
) -> None:
    if not trades:
        return
    statement = (
        "INSERT OR REPLACE INTO trades (symbol, executed_at, trader, action, quantity, price, source) VALUES (?, ?, ?, ?, ?, ?, ?)"
        if replace_existing
        else "INSERT OR IGNORE INTO trades (symbol, executed_at, trader, action, quantity, price, source) VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    payload = [
        (
            symbol,
            trade.executed_at.isoformat(),
            trade.trader,
            trade.action,
            trade.quantity,
            trade.price,
            trade.source,
        )
        for trade in trades
    ]
    conn.executemany(statement, payload)
    conn.commit()


def _next_trades_start_date(conn: sqlite3.Connection, symbol: str, lookback_if_empty_days: int) -> date:
    row = conn.execute("SELECT MAX(executed_at) FROM trades WHERE symbol = ?", (symbol,)).fetchone()
    latest_ts = row[0]
    if latest_ts:
        return datetime.fromisoformat(latest_ts).date()
    return date.today() - timedelta(days=lookback_if_empty_days)
