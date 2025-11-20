"""SQLite-backed readers for cached market, feature, news, and trade data."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
import sqlite3
from typing import Dict, Iterable, List, Optional

from .utils.constants import DATA_DB_PATH


# TODO: @Codex-agent - move this to utils and import everywhere as needed
def _connect(db_path: str = DATA_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    return conn


def fetch_prices(
    symbol: str,
    start: datetime,
    end: datetime,
    interval: str = "1d",
    db_path: str = DATA_DB_PATH,
) -> List[Dict]:
    """Return cached OHLCV rows ordered by timestamp."""
    try:
        with _connect(db_path) as conn:
            rows = conn.execute(
                """
                SELECT ts, open, high, low, close, volume
                FROM prices
                WHERE symbol = ? AND interval = ? AND ts >= ? AND ts <= ?
                ORDER BY ts ASC
                """,
                (symbol, interval, start.isoformat(), end.isoformat()),
            ).fetchall()
    except sqlite3.OperationalError:
        return []
    return [
        {
            "date": ts,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
        }
        for ts, open_price, high_price, low_price, close_price, volume in rows
    ]


def fetch_features(
    symbol: str,
    start: datetime,
    end: datetime,
    interval: str = "1d",
    feature_filter: Optional[Iterable[str]] = None,
    db_path: str = DATA_DB_PATH,
) -> List[Dict]:
    """Return cached feature rows aggregated per timestamp."""
    feature_set = set(feature_filter) if feature_filter else None
    params = [symbol, interval, start.isoformat(), end.isoformat()]
    query = """
        SELECT ts, feature_name, value
        FROM features
        WHERE symbol = ? AND interval = ? AND ts >= ? AND ts <= ?
        ORDER BY ts ASC
    """
    try:
        with _connect(db_path) as conn:
            rows = conn.execute(query, params).fetchall()
    except sqlite3.OperationalError:
        return []

    grouped: Dict[str, Dict] = defaultdict(lambda: {"date": None})
    for ts, name, value in rows:
        if feature_set and name not in feature_set:
            continue
        grouped[ts]["date"] = ts
        grouped[ts][name] = value

    return [grouped[key] for key in sorted(grouped.keys())]


def fetch_news(
    symbol: str,
    start: date,
    end: date,
    db_path: str = DATA_DB_PATH,
) -> List[Dict]:
    """Return cached news rows ordered by publication time."""
    try:
        with _connect(db_path) as conn:
            rows = conn.execute(
                """
                SELECT symbol, published_at, headline, summary, url
                FROM news
                WHERE symbol = ? AND published_at >= ? AND published_at <= ?
                ORDER BY published_at ASC
                """,
                (symbol, start.isoformat(), end.isoformat()),
            ).fetchall()
    except sqlite3.OperationalError:
        return []
    return [
        {
            "symbol": sym,
            "published_at": published_at,
            "headline": headline,
            "summary": summary,
            "url": url,
        }
        for sym, published_at, headline, summary, url in rows
    ]


def fetch_trades(
    symbol: str,
    start: date,
    end: date,
    db_path: str = DATA_DB_PATH,
) -> List[Dict]:
    """Return cached trade disclosures ordered by execution time."""
    try:
        with _connect(db_path) as conn:
            rows = conn.execute(
                """
                SELECT symbol, executed_at, trader, action, quantity, price, source
                FROM trades
                WHERE symbol = ? AND executed_at >= ? AND executed_at <= ?
                ORDER BY executed_at ASC
                """,
                (symbol, start.isoformat(), end.isoformat()),
            ).fetchall()
    except sqlite3.OperationalError:
        return []
    return [
        {
            "symbol": sym,
            "executed_at": executed_at,
            "trader": trader,
            "action": action,
            "quantity": quantity,
            "price": price,
            "source": source,
        }
        for sym, executed_at, trader, action, quantity, price, source in rows
    ]
