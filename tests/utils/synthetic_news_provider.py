"""Synthetic news provider for deterministic testing."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Sequence

from backend.data_provider import NewsArticle, NewsDataProvider


class SyntheticNewsProvider(NewsDataProvider):
    """Returns deterministic news articles within the requested date window."""

    def get_news(self, symbol: str, start_date: date, end_date: date) -> Sequence[NewsArticle]:
        articles = []
        current = start_date
        while current <= end_date:
            published_at = datetime.combine(current, datetime.min.time())
            articles.append(
                NewsArticle(
                    symbol=symbol,
                    headline=f"Headline for {symbol} on {current.isoformat()}",
                    summary=f"Summary for {symbol} on {current.isoformat()}",
                    published_at=published_at,
                    url=f"https://example.com/{symbol}/{current.isoformat()}",
                )
            )
            current += timedelta(days=1)
        return articles
