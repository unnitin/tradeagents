from dataclasses import dataclass
from typing import Dict, List, TypedDict


@dataclass(frozen=True)
class OHLCVResampleRules:
    open: str = "first"
    high: str = "max"
    low: str = "min"
    close: str = "last"
    volume: str = "sum"


# Yahoo Finance API interval mapping
YAHOO_FINANCE_INTERVALS: Dict[str, str] = {
    "1d": "1d",
    "1h": "1h",
    "5m": "5m",
    "1m": "1m",
}


class SampleNewsRecord(TypedDict, total=False):
    published_at: str
    symbol: str
    headline: str
    summary: str
    source: str
    url: str
    sentiment_hint: str


SAMPLE_NEWS: List[SampleNewsRecord] = [
    {
        "published_at": "2024-02-21T09:30:00Z",
        "symbol": "AAPL",
        "headline": "Apple accelerates on-device AI roadmap for iPhone 16",
        "summary": (
            "Bloomberg reports Apple is reallocating silicon budget toward AI features, "
            "lifting supplier expectations."
        ),
        "source": "SampleFeed",
        "url": "https://example.com/apple-ai",
        "sentiment_hint": "bullish",
    },
    {
        "published_at": "2024-02-21T10:15:00Z",
        "symbol": "NVDA",
        "headline": "Senators disclose sizable Nvidia buys ahead of earnings",
        "summary": (
            "Multiple Capitol disclosures show fresh NVDA purchases, intensifying chatter "
            "around the print."
        ),
        "source": "SampleFeed",
        "url": "https://example.com/nvda-politics",
        "sentiment_hint": "bullish",
    },
    {
        "published_at": "2024-02-20T14:45:00Z",
        "symbol": "TSLA",
        "headline": "Tesla faces new EU probe into autonomous claims",
        "summary": (
            "Regulators question Full Self Driving marketing materials, adding pressure to "
            "Tesla's European operations."
        ),
        "source": "SampleFeed",
        "url": "https://example.com/tsla-eu",
        "sentiment_hint": "bearish",
    },
    {
        "published_at": "2024-02-19T12:05:00Z",
        "symbol": "MSFT",
        "headline": "Microsoft integrates Copilot deeper into Teams",
        "summary": (
            "Enterprise preview shows Copilot handling live meeting recaps, driving fresh "
            "subscriptions."
        ),
        "source": "SampleFeed",
        "url": "https://example.com/msft-copilot",
        "sentiment_hint": "bullish",
    },
]


if __name__ == "__main__":
    resample_rules = OHLCVResampleRules()
    print(resample_rules)
