"""Market and news data provider abstractions backed by Yahoo Finance."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import math
from typing import List, Optional, Sequence, Union

try:  # pragma: no cover - optional dependency handled at runtime
    import yfinance as yf
except ImportError:  # pragma: no cover - defer error until provider instantiation
    yf = None  # type: ignore[assignment]

try:  # pragma: no cover - pandas is pulled in by yfinance
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore[assignment]


@dataclass(frozen=True)
class PriceCandle:
    """Represents OHLCV data for a given timestamp (date or intraday)."""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class NewsArticle:
    """Simple structure for future news providers."""

    symbol: str
    headline: str
    summary: str
    published_at: datetime
    url: Optional[str] = None


@dataclass(frozen=True)
class TradeRecord:
    """Represents a disclosed trade (e.g., politician or insider trade)."""

    symbol: str
    trader: str
    action: str  # buy | sell
    quantity: float
    price: Optional[float]
    executed_at: datetime
    source: Optional[str] = None


class MarketDataProvider(ABC):
    """Base interface for market data providers."""

    @abstractmethod
    def get_price_series(
        self, symbol: str, start_date: datetime, end_date: datetime, interval: str = "1d"
    ) -> List[PriceCandle]:
        """Return candles for the requested window and interval (default daily).

        Args:
            symbol: Equity ticker (e.g., AAPL).
            start_date: Inclusive range start as datetime.
            end_date: Inclusive range end as datetime.
            interval: Bar size string supported by the provider.
        """


class NewsDataProvider(ABC):
    """Base interface for news providers."""

    @abstractmethod
    def get_news(self, symbol: str, start_date: date, end_date: date) -> Sequence[NewsArticle]:
        """Return news articles for the requested date window.

        Args:
            symbol: Equity ticker (e.g., AAPL).
            start_date: Inclusive range start date.
            end_date: Inclusive range end date.
        """


class TradeDataProvider(ABC):
    """Base interface for trade disclosure providers."""

    @abstractmethod
    def get_trades(self, symbol: str, start_date: date, end_date: date) -> Sequence["TradeRecord"]:
        """Return trades for the requested date window.

        Args:
            symbol: Equity ticker (e.g., AAPL).
            start_date: Inclusive range start date.
            end_date: Inclusive range end date.
        """


class DataGateway:
    """Central access point for all data domains (market, news, etc.)."""

    def __init__(
        self,
        market_provider: MarketDataProvider,
        news_provider: Optional[NewsDataProvider] = None,
    ) -> None:
        """Store provider dependencies for unified access.

        Args:
            market_provider: Concrete implementation that serves OHLCV data.
            news_provider: Optional implementation that serves news articles.
        """
        self._market_provider = market_provider
        self._news_provider = news_provider

    def get_price_series(
        self, symbol: str, start_date: Union[date, datetime], end_date: Union[date, datetime], interval: str = "1d"
    ) -> List[PriceCandle]:
        """Fetch OHLCV candles for the requested symbol and window.

        Args:
            symbol: Equity ticker (e.g., AAPL).
            start_date: Inclusive start of the window as date or datetime.
            end_date: Inclusive end of the window as date or datetime.
            interval: Bar size such as '1d', '1h', etc.

        Returns:
            Ordered list of PriceCandle rows from the delegated provider.
        """
        start_dt = _to_datetime(start_date)
        end_dt = _to_datetime(end_date)
        return self._market_provider.get_price_series(symbol, start_dt, end_dt, interval=interval)

    def get_news(self, symbol: str, start_date: date, end_date: date) -> Sequence[NewsArticle]:
        """Fetch news articles for the requested symbol and dates.

        Args:
            symbol: Equity ticker (e.g., MSFT).
            start_date: Inclusive start date for filtering articles.
            end_date: Inclusive end date for filtering articles.

        Returns:
            Sequence of NewsArticle items ordered per provider behavior.

        Raises:
            NotImplementedError: If the gateway was not configured with news provider.
        """
        if not self._news_provider:
            raise NotImplementedError("No news provider configured")
        return self._news_provider.get_news(symbol, start_date, end_date)


class YahooMarketDataProvider(MarketDataProvider):
    """Market data provider that fetches bars from Yahoo Finance."""

    def __init__(self, download_fn=None) -> None:
        """Initialize provider with an optional override for yf.download.

        Args:
            download_fn: Function compatible with yfinance.download used for testing.

        Raises:
            ImportError: If yfinance is unavailable in the environment.
        """
        if yf is None:
            raise ImportError("yfinance is required for YahooMarketDataProvider")
        self._download_fn = download_fn or yf.download

    def get_price_series(
        self, symbol: str, start_date: datetime, end_date: datetime, interval: str = "1d"
    ) -> List[PriceCandle]:
        """Return de-duplicated and sanitized Yahoo Finance candles.

        Args:
            symbol: Equity ticker (e.g., AMD).
            start_date: Inclusive window start as datetime.
            end_date: Inclusive window end as datetime.
            interval: Bar size accepted by Yahoo (e.g., '1d', '1h').

        Returns:
            Cleaned list of PriceCandle entries for downstream processing.

        Raises:
            ValueError: If the date range is invalid or Yahoo returns no data.
        """
        if start_date > end_date:
            raise ValueError("start_date must be on or before end_date")

        # yfinance treats the end date as exclusive, so request one extra unit.
        end_inclusive = end_date + timedelta(days=1)
        df = self._download_fn(
            tickers=symbol,
            start=start_date,
            end=end_inclusive,
            interval=interval,
            auto_adjust=False,
            progress=False,
        )

        if df is None or getattr(df, "empty", True):
            raise ValueError(f"No price data returned for {symbol}")

        if pd is not None and isinstance(df.columns, pd.MultiIndex):  # pragma: no cover - defensive
            df = df.xs(symbol, axis=1, level=1)

        candles: List[PriceCandle] = []
        for idx, row in df.iterrows():
            try:
                open_price = float(row["Open"])
                high_price = float(row["High"])
                low_price = float(row["Low"])
                close_price = float(row["Close"])
                volume = int(row["Volume"])
            except KeyError as exc:  # pragma: no cover - schema mismatch
                raise ValueError("Unexpected response format from Yahoo Finance") from exc

            # Skip incomplete rows with NaN OHLC values to avoid leaking gaps into indicators.
            if any(math.isnan(value) for value in (open_price, high_price, low_price, close_price)):
                continue

            # Normalize tz-aware timestamps from yfinance.
            current_ts = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
            candles.append(
                PriceCandle(
                    date=current_ts,
                    open=round(open_price, 4),
                    high=round(high_price, 4),
                    low=round(low_price, 4),
                    close=round(close_price, 4),
                    volume=max(0, volume),
                )
            )

        if not candles:
            raise ValueError(f"Price data unavailable for {symbol} in requested window")

        return candles


class YahooNewsDataProvider(NewsDataProvider):
    """News provider backed by Yahoo Finance news API."""

    def __init__(self, client_factory=None) -> None:
        """Configure provider with optional factory to build Yahoo tickers.

        Args:
            client_factory: Callable returning a yfinance.Ticker-like client.

        Raises:
            ImportError: If yfinance is missing.
        """
        if yf is None:
            raise ImportError("yfinance is required for YahooNewsDataProvider")
        self._client_factory = client_factory or yf.Ticker

    def get_news(self, symbol: str, start_date: date, end_date: date) -> Sequence[NewsArticle]:
        """Return Yahoo Finance news articles filtered by publication date.

        Args:
            symbol: Equity ticker to request from Yahoo's API.
            start_date: Inclusive earliest publication date to include.
            end_date: Inclusive latest publication date to include.

        Returns:
            Sequence of NewsArticle records sorted by Yahoo's ordering.

        Raises:
            ValueError: If start_date occurs after end_date.
        """
        if start_date > end_date:
            raise ValueError("start_date must be on or before end_date")

        ticker = self._client_factory(symbol)
        articles = getattr(ticker, "news", None) or []

        results: List[NewsArticle] = []
        for article in articles:
            published_ts = article.get("providerPublishTime")
            if published_ts is None:
                continue
            published_at = datetime.fromtimestamp(published_ts)
            if not (start_date <= published_at.date() <= end_date):
                continue

            results.append(
                NewsArticle(
                    symbol=symbol,
                    headline=article.get("title", ""),
                    summary=article.get("summary", article.get("text", "")),
                    published_at=published_at,
                    url=article.get("link"),
                )
            )

        return results


def _to_datetime(value: Union[date, datetime]) -> datetime:
    """Normalize date or datetime inputs into a datetime object.

    Args:
        value: Date-like input possibly lacking a time component.

    Returns:
        `datetime` value representing the same instant (dates map to midnight).
    """
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, datetime.min.time())
