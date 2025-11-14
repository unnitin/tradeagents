# Utils Module

Utilities that support every agent and strategy live here. Today the focus is on NLP sentiment scoring, but the folder will grow to house any shared helpers that do not belong in a specific domain module.

## Contents

| File | Responsibility |
| --- | --- |
| `constants.py` | Central place for model names (`FINBERT_MODEL_NAME`, tokenizer IDs, truncation lengths) so we can swap models without touching strategy code. |
| `sentiment_engine.py` | Boots a Hugging Face `pipeline` for FinBERT, exposing `score_sentiment(text)` that returns bullish/bearish/neutral labels plus confidence. |
| `__init__.py` | Re-exports `score_sentiment` to keep imports short (`from utils import score_sentiment`). |

## Usage

```python
from utils import score_sentiment

headline = "NVIDIA beats earnings expectations as demand surges"
sentiment = score_sentiment(headline)

print(sentiment)
# {'label': 'bullish', 'score': 0.92}
```

## Roadmap

- **Additional NLP helpers**: topic classification, news summarisation, or vector store lookups the agents can call.
- **Shared math utils**: risk metrics or position-sizing helpers that should not live inside strategies or the backtest engine.
- **Caching + telemetry**: wrappers that cache expensive model calls and emit timing info for the observability hooks mentioned in the spec.

When in doubt about where a generic helper should live, drop it here so every module can depend on a single implementation.

