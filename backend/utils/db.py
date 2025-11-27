"""SQLite helper utilities shared across data refresh scripts."""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from typing import Iterable, List

from ..data_provider import NewsArticle, PriceCandle, TradeRecord
from ..feature_engineering import compute_features


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def drop_and_create_price_tables(conn: sqlite3.Connection) -> None:
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


def ensure_price_tables(conn: sqlite3.Connection) -> None:
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


def recompute_features(
    conn: sqlite3.Connection, symbol: str, interval: str, feature_names: Iterable[str], *, replace_existing: bool = True
) -> None:
    conn.execute("DELETE FROM features WHERE symbol = ? AND interval = ?;", (symbol, interval))
    cursor = conn.execute(
        "SELECT ts, open, high, low, close, volume FROM prices WHERE symbol = ? AND interval = ? ORDER BY ts ASC;",
        (symbol, interval),
    )
    rows = cursor.fetchall()
    candles: List[PriceCandle] = [
        PriceCandle(
            date=datetime.fromisoformat(ts),
            open=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
        )
        for ts, open_, high, low, close, volume in rows
    ]
    computed = compute_features(candles, list(feature_names))
    feature_rows = [
        (symbol, row["date"], interval, feature_name, value)
        for row in computed
        for feature_name, value in row.items()
        if feature_name != "date"
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO features (symbol, ts, interval, feature_name, value) VALUES (?, ?, ?, ?, ?);",
        feature_rows,
    )


def next_start_timestamp(conn: sqlite3.Connection, symbol: str, interval: str, lookback_if_empty_days: int) -> datetime:
    cursor = conn.execute(
        "SELECT MAX(ts) FROM prices WHERE symbol = ? AND interval = ?;",
        (symbol, interval),
    )
    result = cursor.fetchone()[0]
    if result is None:
        return datetime.utcnow() - timedelta(days=lookback_if_empty_days)
    return datetime.fromisoformat(result)


def upsert_prices(conn: sqlite3.Connection, symbol: str, interval: str, candles: Iterable[PriceCandle], *, replace_existing: bool) -> None:
    rows = [
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
    sql = "INSERT OR REPLACE INTO prices (symbol, ts, interval, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?, ?);" if replace_existing else "INSERT OR IGNORE INTO prices (symbol, ts, interval, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
    conn.executemany(sql, rows)


def drop_and_create_news_table(conn: sqlite3.Connection) -> None:
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


def ensure_news_table(conn: sqlite3.Connection) -> None:
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


def upsert_news(conn: sqlite3.Connection, symbol: str, articles: Iterable[NewsArticle], *, replace_existing: bool) -> None:
    rows = [(symbol, article.published_at.isoformat(), article.headline, article.summary, article.url) for article in articles]
    sql = "INSERT OR REPLACE INTO news (symbol, published_at, headline, summary, url) VALUES (?, ?, ?, ?, ?);" if replace_existing else "INSERT OR IGNORE INTO news (symbol, published_at, headline, summary, url) VALUES (?, ?, ?, ?, ?);"
    conn.executemany(sql, rows)


def drop_and_create_trades_table(conn: sqlite3.Connection) -> None:
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
            PRIMARY KEY (symbol, executed_at, trader, action)
        );
        """
    )


def ensure_trades_table(conn: sqlite3.Connection) -> None:
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
            PRIMARY KEY (symbol, executed_at, trader, action)
        );
        """
    )


def upsert_trades(conn: sqlite3.Connection, symbol: str, trades: Iterable[TradeRecord], *, replace_existing: bool) -> None:
    rows = [
        (symbol, trade.executed_at.isoformat(), trade.trader, trade.action, trade.quantity, trade.price, trade.source) for trade in trades
    ]
    sql = "INSERT OR REPLACE INTO trades (symbol, executed_at, trader, action, quantity, price, source) VALUES (?, ?, ?, ?, ?, ?, ?);" if replace_existing else "INSERT OR IGNORE INTO trades (symbol, executed_at, trader, action, quantity, price, source) VALUES (?, ?, ?, ?, ?, ?, ?);"
    conn.executemany(sql, rows)


def next_news_start_date(conn: sqlite3.Connection, symbol: str, lookback_if_empty_days: int) -> date:
    cursor = conn.execute("SELECT MAX(published_at) FROM news WHERE symbol = ?;", (symbol,))
    result = cursor.fetchone()[0]
    if result is None:
        return datetime.utcnow().date() - timedelta(days=lookback_if_empty_days)
    return datetime.fromisoformat(result).date()


def next_trades_start_date(conn: sqlite3.Connection, symbol: str, lookback_if_empty_days: int) -> date:
    cursor = conn.execute("SELECT MAX(executed_at) FROM trades WHERE symbol = ?;", (symbol,))
    result = cursor.fetchone()[0]
    if result is None:
        return datetime.utcnow().date() - timedelta(days=lookback_if_empty_days)
    return datetime.fromisoformat(result).date()
