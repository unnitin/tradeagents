"""Flask application that exposes market data and feature engineering APIs."""
from __future__ import annotations

from datetime import date, datetime
from http import HTTPStatus
from typing import Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, abort, jsonify, request
from werkzeug.exceptions import HTTPException

from .utils.constants import DATE_FORMAT, DATA_DB_PATH
from .data_provider import (
    DataGateway,
    MarketDataProvider,
    NewsDataProvider,
    TradeDataProvider,
    YahooMarketDataProvider,
    YahooNewsDataProvider,
)
from .feature_engineering import FeatureEngineeringError, compute_features
from .utils import data_refresh
from .storage import fetch_features, fetch_news, fetch_prices, fetch_trades


def create_app(
    market_provider: Optional[MarketDataProvider] = None,
    news_provider: Optional[NewsDataProvider] = None,
    trade_provider: Optional[TradeDataProvider] = None,
    db_path: str = DATA_DB_PATH,
) -> Flask:
    app = Flask(__name__)
    executor = ThreadPoolExecutor(max_workers=3)
    selected_news_provider = news_provider
    if selected_news_provider is None and YahooNewsDataProvider is not None:
        try:
            selected_news_provider = YahooNewsDataProvider()
        except ImportError:
            selected_news_provider = None

    data_gateway = DataGateway(
        market_provider or YahooMarketDataProvider(),
        news_provider=selected_news_provider,
    )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        response = jsonify({"error": error.description, "code": error.code})
        response.status_code = error.code
        return response

    @app.errorhandler(FeatureEngineeringError)
    def handle_feature_error(error: FeatureEngineeringError):
        response = jsonify({"error": str(error), "code": HTTPStatus.BAD_REQUEST})
        response.status_code = HTTPStatus.BAD_REQUEST
        return response

    @app.get("/health")
    def health() -> Any:
        """Health check endpoint returning service status."""
        return {"status": "ok"}

    # Returns historical OHLCV data for a symbol over a date range.
    @app.get("/data/prices")
    def get_prices() -> Any:
        """
        Query params:
        - symbol: required ticker symbol (e.g., AAPL).
        - start_date: required ISO date (YYYY-MM-DD) inclusive.
        - end_date: required ISO date (YYYY-MM-DD) inclusive.

        Returns JSON with symbol and list of OHLCV price records.
        """
        symbol = request.args.get("symbol", type=str)
        start_raw = request.args.get("start_date", type=str)
        end_raw = request.args.get("end_date", type=str)

        if not symbol or not start_raw or not end_raw:
            abort(HTTPStatus.BAD_REQUEST, description="symbol, start_date, and end_date are required")

        start_date = _parse_date(start_raw)
        end_date = _parse_date(end_raw)

        try:
            candles = data_gateway.get_price_series(symbol, start_date, end_date)
        except ValueError as exc:
            abort(HTTPStatus.BAD_REQUEST, description=str(exc))

        return {
            "symbol": symbol,
            "prices": [
                {
                    "date": candle.date.isoformat(),
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                }
                for candle in candles
            ],
        }

    # Computes requested indicators/features over a symbol's price history.
    @app.post("/features")
    def create_features() -> Any:
        """
        Body (JSON):
        - symbol: required ticker symbol (e.g., MSFT).
        - start_date: required ISO date (YYYY-MM-DD) inclusive.
        - end_date: required ISO date (YYYY-MM-DD) inclusive.
        - features: required list of indicator names (e.g., ["sma_10", "ema_5", "return_pct"]).

        Returns JSON with symbol and per-day rows containing requested feature values.
        """
        payload = request.get_json(silent=True) or {}
        symbol = payload.get("symbol")
        start_raw = payload.get("start_date")
        end_raw = payload.get("end_date")
        feature_names = payload.get("features")

        if not symbol or not start_raw or not end_raw:
            abort(HTTPStatus.BAD_REQUEST, description="symbol, start_date, and end_date are required")
        if not isinstance(feature_names, list) or not all(isinstance(name, str) for name in feature_names):
            abort(HTTPStatus.BAD_REQUEST, description="features must be a list of strings")

        start_date = _parse_date(start_raw)
        end_date = _parse_date(end_raw)

        try:
            candles = data_gateway.get_price_series(symbol, start_date, end_date)
        except ValueError as exc:
            abort(HTTPStatus.BAD_REQUEST, description=str(exc))

        feature_rows = compute_features(candles, feature_names)

        return {"symbol": symbol, "features": feature_rows}

    # Reads cached OHLCV rows from SQLite.
    @app.get("/cache/prices")
    def read_cached_prices() -> Any:
        """Serve cached OHLCV rows from SQLite for a symbol/date range and interval.

        Query params:
        - symbol: required ticker symbol (e.g., AAPL).
        - start_date: required ISO date (YYYY-MM-DD) inclusive.
        - end_date: required ISO date (YYYY-MM-DD) inclusive.
        - interval: optional bar size (default 1d).
        """
        symbol = request.args.get("symbol", type=str)
        start_raw = request.args.get("start_date", type=str)
        end_raw = request.args.get("end_date", type=str)
        interval = request.args.get("interval", default="1d", type=str)
        if not symbol or not start_raw or not end_raw:
            abort(HTTPStatus.BAD_REQUEST, description="symbol, start_date, and end_date are required")
        start_dt = _parse_date(start_raw)
        end_dt = _parse_date(end_raw)
        prices = fetch_prices(symbol, _to_datetime(start_dt), _to_datetime(end_dt), interval=interval, db_path=db_path)
        return {"symbol": symbol, "interval": interval, "prices": prices}

    # Reads cached features from SQLite (optionally filtered by feature names).
    @app.get("/cache/features")
    def read_cached_features() -> Any:
        """Serve cached feature rows from SQLite for a symbol/date range and interval.

        Query params:
        - symbol: required ticker symbol (e.g., AAPL).
        - start_date: required ISO date (YYYY-MM-DD) inclusive.
        - end_date: required ISO date (YYYY-MM-DD) inclusive.
        - interval: optional bar size (default 1d).
        - feature: optional repeated query param to filter specific feature names.
        """
        symbol = request.args.get("symbol", type=str)
        start_raw = request.args.get("start_date", type=str)
        end_raw = request.args.get("end_date", type=str)
        interval = request.args.get("interval", default="1d", type=str)
        features_filter = request.args.getlist("feature")
        if not symbol or not start_raw or not end_raw:
            abort(HTTPStatus.BAD_REQUEST, description="symbol, start_date, and end_date are required")
        start_dt = _parse_date(start_raw)
        end_dt = _parse_date(end_raw)
        features = fetch_features(
            symbol,
            _to_datetime(start_dt),
            _to_datetime(end_dt),
            interval=interval,
            feature_filter=features_filter or None,
            db_path=db_path,
        )
        return {"symbol": symbol, "interval": interval, "features": features}

    # Reads cached news articles from SQLite.
    @app.get("/cache/news")
    def read_cached_news() -> Any:
        """Serve cached news articles from SQLite for a symbol and date range.

        Query params:
        - symbol: required ticker symbol.
        - start_date: required ISO date (YYYY-MM-DD) inclusive.
        - end_date: required ISO date (YYYY-MM-DD) inclusive.
        """
        symbol = request.args.get("symbol", type=str)
        start_raw = request.args.get("start_date", type=str)
        end_raw = request.args.get("end_date", type=str)
        if not symbol or not start_raw or not end_raw:
            abort(HTTPStatus.BAD_REQUEST, description="symbol, start_date, and end_date are required")
        start_date = _parse_date(start_raw)
        end_date = _parse_date(end_raw)
        news_rows = fetch_news(symbol, start_date, end_date, db_path=db_path)
        return {"symbol": symbol, "news": news_rows}

    # Reads cached trade disclosures from SQLite.
    @app.get("/cache/trades")
    def read_cached_trades() -> Any:
        """Serve cached trade disclosures from SQLite for a symbol and date range.

        Query params:
        - symbol: required ticker symbol.
        - start_date: required ISO date (YYYY-MM-DD) inclusive.
        - end_date: required ISO date (YYYY-MM-DD) inclusive.
        """
        symbol = request.args.get("symbol", type=str)
        start_raw = request.args.get("start_date", type=str)
        end_raw = request.args.get("end_date", type=str)
        if not symbol or not start_raw or not end_raw:
            abort(HTTPStatus.BAD_REQUEST, description="symbol, start_date, and end_date are required")
        start_date = _parse_date(start_raw)
        end_date = _parse_date(end_raw)
        trades_rows = fetch_trades(symbol, start_date, end_date, db_path=db_path)
        return {"symbol": symbol, "trades": trades_rows}

    # Triggers incremental refresh of cached data using configured providers.
    @app.post("/refresh")
    def refresh_cache() -> Any:
        """Trigger incremental refresh of cached prices/features and optional news/trades.

        Body (JSON):
        - symbols: required list of ticker symbols.
        - interval: optional bar size for prices (default 1d).
        - features: optional list of feature names to recompute.
        - refresh_news: optional bool to also refresh news cache.
        - refresh_trades: optional bool to also refresh trade cache.
        - lookback_days: optional int lookback if caches are empty (default 5).
        """
        payload = request.get_json(silent=True) or {}
        symbols = payload.get("symbols")
        interval = payload.get("interval", "1d")
        feature_names = payload.get("features")
        refresh_news = payload.get("refresh_news", False)
        refresh_trades = payload.get("refresh_trades", False)
        lookback = int(payload.get("lookback_days", 5))

        if not symbols or not isinstance(symbols, list):
            abort(HTTPStatus.BAD_REQUEST, description="symbols must be a non-empty list of tickers")

        jobs = [
            (
                data_refresh.run_incremental_update_prices,
                dict(
                    provider=data_gateway._market_provider,
                    symbols=symbols,
                    interval=interval,
                    feature_names=feature_names,
                    db_path=db_path,
                    lookback_if_empty_days=lookback,
                ),
            )
        ]

        if refresh_news and data_gateway._news_provider:
            jobs.append(
                (
                    data_refresh.run_incremental_update_news,
                    dict(
                        symbols=symbols,
                        db_path=db_path,
                        news_provider=data_gateway._news_provider,
                        lookback_if_empty_days=lookback,
                    ),
                )
            )

        if refresh_trades and trade_provider:
            jobs.append(
                (
                    data_refresh.run_incremental_update_trades,
                    dict(
                        symbols=symbols,
                        db_path=db_path,
                        trade_provider=trade_provider,
                        lookback_if_empty_days=lookback,
                    ),
                )
            )

        try:
            if app.config.get("TESTING"):
                for func, kwargs in jobs:
                    func(**kwargs)
            else:
                for func, kwargs in jobs:
                    executor.submit(func, **kwargs)
        except ValueError as exc:
            abort(HTTPStatus.BAD_REQUEST, description=str(exc))

        return {"status": "accepted"}

    return app


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError as exc:
        abort(HTTPStatus.BAD_REQUEST, description=f"invalid date '{value}' (expected YYYY-MM-DD)")


def _to_datetime(value: date) -> datetime:
    return datetime.combine(value, datetime.min.time())
