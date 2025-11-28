"""Tests for data provider utilities."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

import pytest

from backend.data_provider import FinnhubNewsDataProvider, NewsArticle


class _DummyResponse:
    def __init__(self, payload: List[Dict[str, Any]], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")

    def json(self) -> List[Dict[str, Any]]:
        return self._payload


class _RecordingSession:
    def __init__(self, responses: List[_DummyResponse]) -> None:
        self._responses = responses
        self.calls: List[Dict[str, Any]] = []

    def get(self, url: str, params: Dict[str, Any], timeout: int) -> _DummyResponse:
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        response = self._responses.pop(0)
        return response


def test_finnhub_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure Finnhub provider fails fast without an API key."""
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    provider = FinnhubNewsDataProvider(session=_RecordingSession([]), base_url="https://example.test")

    with pytest.raises(ValueError, match="Finnhub API key is required"):
        provider.get_news("AAPL", date(2024, 1, 1), date(2024, 1, 2))


def test_finnhub_provider_fetches_and_transforms_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify Finnhub provider builds the right request and emits NewsArticle rows."""
    payload = [
        {
            "headline": "Sample",
            "summary": "Details",
            "datetime": int(datetime(2024, 1, 1, 15, 30).timestamp()),
            "url": "https://example.test/article",
        }
    ]
    session = _RecordingSession([_DummyResponse(payload)])
    provider = FinnhubNewsDataProvider(api_key="xyz", session=session, base_url="https://example.test/api")

    articles = provider.get_news("MSFT", date(2024, 1, 1), date(2024, 1, 3))

    assert len(articles) == 1
    article = articles[0]
    assert isinstance(article, NewsArticle)
    assert article.symbol == "MSFT"
    assert article.headline == "Sample"
    assert article.summary == "Details"
    assert article.url == "https://example.test/article"

    assert session.calls, "Expected session.get to be invoked"
    call = session.calls[0]
    assert call["url"] == "https://example.test/api/company-news"
    assert call["params"] == {
        "symbol": "MSFT",
        "from": "2024-01-01",
        "to": "2024-01-03",
        "token": "xyz",
    }


def test_finnhub_provider_retries_rate_limited_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure provider retries when Finnhub responds with 429."""
    payload = [
        {
            "headline": "Recovered",
            "summary": "",
            "datetime": int(datetime(2024, 2, 1, 12).timestamp()),
            "url": "https://example.test/recovered",
        }
    ]
    session = _RecordingSession([
        _DummyResponse([], status_code=429),
        _DummyResponse(payload, status_code=200),
    ])
    monkeypatch.setattr("backend.data_provider.time.sleep", lambda _delay: None)
    provider = FinnhubNewsDataProvider(
        api_key="xyz",
        session=session,
        base_url="https://example.test/api",
        rate_limit_retry_delay=0.1,
        max_rate_limit_retries=2,
    )

    articles = provider.get_news("AAPL", date(2024, 2, 1), date(2024, 2, 2))

    assert len(articles) == 1
    assert len(session.calls) == 2, "Expected the provider to retry after 429"
    assert articles[0].headline == "Recovered"
