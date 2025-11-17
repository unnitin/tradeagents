from datetime import date, timedelta
import time

import pytest

from backend import create_app
from backend import automation, storage
from tests.utils.synthetic_data_provider import SyntheticMarketDataProvider
from tests.utils.synthetic_news_provider import SyntheticNewsProvider
from tests.utils.synthetic_trade_provider import SyntheticTradeProvider


@pytest.fixture()
def temp_db(tmp_path):
    """Temporary SQLite path for isolation per test.

    Args:
        tmp_path: pytest-provided temporary directory fixture.
    Returns:
        Path to a sqlite file used by a single test.
    """
    return tmp_path / "data.db"


@pytest.fixture()
def app_client(temp_db):
    """Flask test client wired to synthetic providers and temp DB.

    Args:
        temp_db: path to the temporary sqlite database for this test.
    Returns:
        Flask test client configured with synthetic providers and temp DB.
    """
    market_provider = SyntheticMarketDataProvider()
    news_provider = SyntheticNewsProvider()
    trade_provider = SyntheticTradeProvider()
    app = create_app(
        market_provider=market_provider,
        news_provider=news_provider,
        trade_provider=trade_provider,
        db_path=str(temp_db),
    )
    app.config.update(TESTING=True)
    return app.test_client()


def test_run_backfill_prices_populates_db(temp_db):
    """Backfill writes OHLCV rows and expected fields into SQLite.

    Uses SyntheticMarketDataProvider and checks required OHLCV keys in the DB.
    """
    provider = SyntheticMarketDataProvider()
    start_date = date.today() - timedelta(days=3)
    automation.run_backfill_prices(
        provider=provider,
        symbols=["AAPL"],
        days=3,
        interval="1d",
        db_path=str(temp_db),
    )

    prices = storage.fetch_prices(
        "AAPL",
        start=start_date,
        end=date.today(),
        interval="1d",
        db_path=str(temp_db),
    )
    assert len(prices) >= 3
    assert {"open", "high", "low", "close", "volume"}.issubset(prices[0].keys())


def test_refresh_endpoint_triggers_updates(app_client, temp_db):
    """Refresh endpoint accepts and background job populates cache.

    Posts a refresh payload with symbols/interval/lookback and polls the cache DB.
    """
    start_date = date.today() - timedelta(days=2)
    end_date = date.today()
    payload = {
        "symbols": ["MSFT"],
        "interval": "1d",
        "lookback_days": 2,
        "refresh_news": True,
        "refresh_trades": True,
    }
    resp = app_client.post("/refresh", json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "accepted"

    # Poll cache until data is written by background tasks.
    for _ in range(10):
        prices = storage.fetch_prices("MSFT", start=start_date, end=end_date, interval="1d", db_path=str(temp_db))
        if prices:
            break
        time.sleep(0.1)
    assert prices, "expected prices to be cached after refresh"

    news_rows = storage.fetch_news("MSFT", start_date=start_date, end_date=end_date, db_path=str(temp_db))
    trades_rows = storage.fetch_trades("MSFT", start_date=start_date, end_date=end_date, db_path=str(temp_db))
    assert news_rows
    assert trades_rows


def test_cache_endpoints_validate_input(app_client):
    """Cache endpoints reject missing or malformed inputs.

    Asserts 400 responses when required params are absent or invalid.
    """
    resp = app_client.get("/cache/prices", query_string={})
    assert resp.status_code == 400
    resp = app_client.get("/cache/features", query_string={"symbol": "AAPL", "start_date": "2024-01-01"})
    assert resp.status_code == 400
    resp = app_client.get("/cache/news", query_string={"symbol": "AAPL", "start_date": "bad", "end_date": "2024-01-02"})
    assert resp.status_code == 400


def test_incremental_prices_creates_tables_when_empty(temp_db):
    """Incremental update seeds tables when empty using synthetic provider.

    Runs the incremental job with lookback_days and asserts cached prices exist.
    """
    provider = SyntheticMarketDataProvider()
    automation.run_incremental_update_prices(
        provider=provider,
        symbols=["GOOG"],
        interval="1d",
        db_path=str(temp_db),
        lookback_if_empty_days=2,
    )
    prices = storage.fetch_prices("GOOG", start=date.today() - timedelta(days=2), end=date.today(), db_path=str(temp_db))
    assert prices
