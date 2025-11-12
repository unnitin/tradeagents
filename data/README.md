# 📊 Data Module

The `data/` package is the system’s ingestion and feature layer. It fulfills the spec’s requirements for multi-source data (prices, alternative data, and news) and prepares indicator-enriched tables for every downstream agent.

## Responsibilities

| File | Highlights |
| --- | --- |
| `fetch_data.py` | `DataFetcher` that pulls OHLCV from Yahoo Finance, top-10 crypto, and Quiver Quant’s politician trade API. Handles caching, retries, and schema normalization. |
| `news.py` | Hooks for ingesting or simulating news/social data. Provides helper methods the sentiment agents can call until a live API key is configured. |
| `preprocess.py` | Resampling helpers for daily/hourly aggregation, tied to `constants.OHLCV_RESAMPLE_RULES`. |
| `features.py` | Adds all core indicators (SMA, EMA, RSI, Bollinger Bands, MACD, ATR, etc.) to a price frame in one place. |
| `constants.py` | Source of truth for API endpoints, resample intervals, FinBERT config names, and default indicator settings. |

## Feature Engineering Cheatsheet

All functions live in `features.py` and are designed to be chained:

| Function | Purpose | Typical Usage |
| --- | --- | --- |
| `add_sma(df, window=20)` | Rolling average of close price | Trend direction, crossover logic |
| `add_ema(df, window=20)` | Faster weighted average | Momentum + MACD calculations |
| `add_rsi(df, window=14)` | Momentum oscillator | Mean-reversion triggers (RSI < 30) |
| `add_bollinger_bands(df, window=20, num_std=2.0)` | Volatility envelopes | Breakout/bounce strategies |
| `add_macd(df, fast=12, slow=26, signal=9)` | Momentum differential | Detect bullish/bearish crossovers |
| `add_atr(df, window=14)` | Average True Range | Position sizing, volatility filters |

Use `apply_feature_pipeline(df)` to compute the standard indicator set in one call.

## Alternative Data + News

```python
from data.fetch_data import DataFetcher

fetcher = DataFetcher()
price_df = fetcher.get_price_data("AAPL", interval="1d", lookback_days=365)
politician_trades = fetcher.get_politician_trades(chamber="both", days_back=30)
news_df = fetcher.get_news_sentiment_stub(symbols=["AAPL", "MSFT"])
```

The fetched frames are stored in `AgentContext.data` under keys such as `price_data`, `politician_trades`, and `news_data`, so agents/strategies can consume them without duplicating IO logic.

## Pipeline Example

```python
from data.fetch_data import DataFetcher
from data.features import add_rsi, add_macd, add_atr

fetcher = DataFetcher()
df = fetcher.get_price_data("MSFT", interval="1h", lookback_days=120)
df = add_rsi(add_macd(add_atr(df)))
df = df.dropna()
```

This module underpins every other layer—keep it deterministic, well-tested, and aligned with the guardrails described in the technical spec.
