"""Automation entrypoints that wrap utility backfill/update helpers.

This module delegates to `backend.utils.data_refresh` and provides a simple
`seed_dev_data` helper to quickly populate the local SQLite cache when
bringing up a dev instance.
"""
from __future__ import annotations

from typing import Iterable, Sequence

from .data_provider import TradeDataProvider, YahooMarketDataProvider, YahooNewsDataProvider
from .utils import data_refresh
from .utils.constants import DATA_DB_PATH, PRICE_DEFAULT_FEATURES
from .utils.config_parser import load_automation_config

# Re-export utility functions for compatibility with existing imports.
run_backfill_prices = data_refresh.run_backfill_prices
run_incremental_update_prices = data_refresh.run_incremental_update_prices
run_backfill_news = data_refresh.run_backfill_news
run_incremental_update_news = data_refresh.run_incremental_update_news
run_backfill_trades = data_refresh.run_backfill_trades
run_incremental_update_trades = data_refresh.run_incremental_update_trades
run_backfill = data_refresh.run_backfill
run_incremental_update = data_refresh.run_incremental_update


def seed_dev_data(
    symbols: Sequence[str] = ("AAPL", "MSFT", "NVDA"),
    *,
    days: int = 30,
    interval: str = "1d",
    feature_names: Iterable[str] | None = PRICE_DEFAULT_FEATURES,
    db_path: str = DATA_DB_PATH,
    include_news: bool = False,
    include_trades: bool = False,
) -> None:
    """Seed the local SQLite cache with prices/features (and optionally news/trades)."""
    market_provider = YahooMarketDataProvider()
    news_provider = YahooNewsDataProvider() if include_news else None
    trade_provider: TradeDataProvider | None = None

    data_refresh.run_backfill_prices(
        provider=market_provider,
        symbols=symbols,
        days=days,
        interval=interval,
        feature_names=feature_names,
        db_path=db_path,
    )

    if include_news and news_provider:
        data_refresh.run_backfill_news(
            symbols=symbols,
            days=days,
            db_path=db_path,
            news_provider=news_provider,
        )

    if include_trades and trade_provider:
        data_refresh.run_backfill_trades(
            symbols=symbols,
            days=days,
            db_path=db_path,
            trade_provider=trade_provider,
        )


def seed_from_config(env: str = "dev") -> None:
    cfg = load_automation_config(env)
    price_cfg = cfg.price
    storage_cfg = cfg.storage

    seed_dev_data(
        symbols=tuple(price_cfg.tickers),
        days=int(price_cfg.lookback_days),
        interval=price_cfg.interval,
        db_path=storage_cfg.path or DATA_DB_PATH,
        include_news=bool(cfg.news.provider),
        include_trades=bool(cfg.trades.provider),
    )


if __name__ == "__main__":
    seed_from_config()
