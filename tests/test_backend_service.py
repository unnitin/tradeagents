import pytest

from backend import create_app
from tests.utils.synthetic_data_provider import SyntheticMarketDataProvider


@pytest.fixture()
def client():
    app = create_app(market_provider=SyntheticMarketDataProvider())
    app.config.update(TESTING=True)
    return app.test_client()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_get_prices_returns_series(client):
    response = client.get("/data/prices", query_string={"symbol": "AAPL", "start_date": "2024-01-01", "end_date": "2024-01-05"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["symbol"] == "AAPL"
    assert len(payload["prices"]) == 5
    assert {"open", "high", "low", "close", "volume"}.issubset(payload["prices"][0].keys())


def test_get_prices_validates_dates(client):
    response = client.get("/data/prices", query_string={"symbol": "AAPL", "start_date": "2024-01-10", "end_date": "2024-01-01"})
    assert response.status_code == 400
    assert "start_date" in response.get_json()["error"]


def test_create_features_returns_requested_indicators(client):
    response = client.post(
        "/features",
        json={
            "symbol": "MSFT",
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "features": ["sma_3", "ema_5", "return_pct", "volatility_3"],
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["symbol"] == "MSFT"
    assert len(payload["features"]) == 7
    feature_row = payload["features"][3]
    assert "sma_3" in feature_row and "ema_5" in feature_row


def test_create_features_rejects_unknown_feature(client):
    response = client.post(
        "/features",
        json={
            "symbol": "MSFT",
            "start_date": "2024-01-01",
            "end_date": "2024-01-03",
            "features": ["unknown"],
        },
    )
    assert response.status_code == 400
    assert "unsupported" in response.get_json()["error"]
