"""
News ingestion utilities for AstraQuant.

Provides a NewsFetcher that pulls structured headlines either from live APIs
or from deterministic sample data when API keys are unavailable. The output
schema is designed to plug directly into sentiment strategies that expect a
`news_headline` column for scoring.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List, Optional

import pandas as pd
import requests

from data.constants import SAMPLE_NEWS


@dataclass
class NewsFetcher:
    """
    Fetches financial news headlines from external APIs with graceful fallbacks.

    Supported providers:
        - NewsAPI (https://newsapi.org) via NEWSAPI_API_KEY
        - Finnhub company-news endpoint via FINNHUB_API_KEY
    """

    newsapi_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None

    def __post_init__(self) -> None:
        if self.newsapi_api_key is None:
            self.newsapi_api_key = os.getenv("NEWSAPI_API_KEY")
        if self.finnhub_api_key is None:
            self.finnhub_api_key = os.getenv("FINNHUB_API_KEY")
        self._session = requests.Session()

    def get_headlines(
        self,
        symbols: Optional[Iterable[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        provider: str = "newsapi",
    ) -> pd.DataFrame:
        """
        Retrieve news headlines for the requested symbols/time range.

        Args:
            symbols: Iterable of tickers (defaults to sample tickers if None).
            start_date: ISO date string; defaults to 3 days ago.
            end_date: ISO date string; defaults to today.
            limit: Max number of articles to return.
            provider: Preferred provider ("newsapi" or "finnhub").
        """
        symbols = list(symbols) if symbols else ["AAPL", "MSFT", "NVDA"]
        start_dt = self._parse_date(start_date) or (datetime.utcnow() - timedelta(days=3))
        end_dt = self._parse_date(end_date) or datetime.utcnow()

        fetchers = {
            "newsapi": self._fetch_newsapi,
            "finnhub": self._fetch_finnhub,
        }

        fetcher = fetchers.get(provider, self._fetch_newsapi)
        df = fetcher(symbols, start_dt, end_dt, limit)

        if df.empty:
            df = self._fallback_sample(symbols, start_dt, end_dt, limit)

        return self._format_output(df, symbols)

    def _fetch_newsapi(
        self,
        symbols: List[str],
        start_dt: datetime,
        end_dt: datetime,
        limit: int,
    ) -> pd.DataFrame:
        if not self.newsapi_api_key:
            return pd.DataFrame()

        query = " OR ".join(symbols)
        params = {
            "q": query,
            "from": start_dt.isoformat(timespec="seconds"),
            "to": end_dt.isoformat(timespec="seconds"),
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(limit, 100),
        }
        headers = {"Authorization": self.newsapi_api_key}

        try:
            resp = self._session.get(
                "https://newsapi.org/v2/everything",
                params=params,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
        except Exception:
            return pd.DataFrame()

        records = []
        for article in articles:
            records.append(
                {
                    "published_at": article.get("publishedAt"),
                    "headline": article.get("title"),
                    "summary": article.get("description"),
                    "source": (article.get("source") or {}).get("name"),
                    "url": article.get("url"),
                    "symbols": symbols,
                }
            )
        return pd.DataFrame(records)

    def _fetch_finnhub(
        self,
        symbols: List[str],
        start_dt: datetime,
        end_dt: datetime,
        limit: int,
    ) -> pd.DataFrame:
        if not self.finnhub_api_key:
            return pd.DataFrame()

        records: List[dict] = []
        for symbol in symbols:
            params = {
                "symbol": symbol,
                "from": start_dt.date().isoformat(),
                "to": end_dt.date().isoformat(),
                "token": self.finnhub_api_key,
            }
            try:
                resp = self._session.get(
                    "https://finnhub.io/api/v1/company-news",
                    params=params,
                    timeout=30,
                )
                resp.raise_for_status()
                news_items = resp.json()
            except Exception:
                continue

            for item in news_items[: limit // max(len(symbols), 1)]:
                records.append(
                    {
                        "published_at": datetime.utcfromtimestamp(
                            item.get("datetime", 0)
                        ).isoformat(),
                        "headline": item.get("headline"),
                        "summary": item.get("summary"),
                        "source": item.get("source"),
                        "url": item.get("url"),
                        "symbols": [symbol],
                    }
                )
        return pd.DataFrame(records)

    def _fallback_sample(
        self,
        symbols: List[str],
        start_dt: datetime,
        end_dt: datetime,
        limit: int,
    ) -> pd.DataFrame:
        df = pd.DataFrame(SAMPLE_NEWS)
        df["published_at"] = pd.to_datetime(df["published_at"])
        mask = (df["published_at"] >= start_dt) & (df["published_at"] <= end_dt)
        df = df[mask]
        df = df[df["symbol"].isin(symbols)]
        return df.head(limit)

    def _format_output(self, df: pd.DataFrame, symbols: List[str]) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(
                columns=[
                    "published_at",
                    "symbol",
                    "headline",
                    "summary",
                    "source",
                    "url",
                    "news_headline",
                ]
            )

        df = df.copy()
        if "symbol" not in df.columns:
            df["symbol"] = df.get("symbols").apply(
                lambda vals: vals[0] if isinstance(vals, list) and vals else symbols[0]
            )
        df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
        df = df.dropna(subset=["published_at"])
        df["news_headline"] = df["headline"]
        df["date"] = df["published_at"].dt.date
        df["symbol"] = df["symbol"].str.upper()
        return df.sort_values("published_at", ascending=False).reset_index(drop=True)

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            return None


__all__ = ["NewsFetcher", "SAMPLE_NEWS"]
