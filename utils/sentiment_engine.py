"""Sentiment scoring helpers with optional offline mock support."""

from __future__ import annotations

import os
from typing import Dict

from transformers import pipeline

from .constants import (
    FINBERT_MODEL_NAME,
    FINBERT_TOKENIZER,
    SENTIMENT_TRUNCATE_CHARS,
)


def _load_transformer_pipeline():
    return pipeline(
        "sentiment-analysis",
        model=FINBERT_MODEL_NAME,
        tokenizer=FINBERT_TOKENIZER,
    )


def _mock_sentiment(text: str) -> Dict[str, float]:
    lowered = text.lower()
    bullish_tokens = ("beat", "surge", "record", "upgrade", "buyback", "beats")
    bearish_tokens = ("miss", "downgrade", "probe", "selloff", "cut", "lawsuit")

    if any(token in lowered for token in bullish_tokens):
        return {"label": "bullish", "score": 0.8}
    if any(token in lowered for token in bearish_tokens):
        return {"label": "bearish", "score": 0.8}
    return {"label": "neutral", "score": 0.0}


USE_MOCK_SENTIMENT = os.getenv("ASTRAQUANT_SENTIMENT_MODE", "").lower() == "mock"
sentiment_pipeline = None
pipeline_error = None

if not USE_MOCK_SENTIMENT:
    try:
        sentiment_pipeline = _load_transformer_pipeline()
    except Exception as exc:  # pragma: no cover - fallback path
        pipeline_error = str(exc)
        USE_MOCK_SENTIMENT = True


def score_sentiment(text: str = None) -> dict:
    """
    Classifies sentiment of financial text into bullish, bearish, or neutral.

    Args:
        text (str): Market text or headline snippet.

    Returns:
        dict: {
            'label': 'bullish' | 'bearish' | 'neutral',
            'score': float (confidence),
        }
    """
    if not text or not isinstance(text, str):
        return {"label": "neutral", "score": 0.0}

    if USE_MOCK_SENTIMENT or sentiment_pipeline is None:
        return _mock_sentiment(text)

    result = sentiment_pipeline(text[:SENTIMENT_TRUNCATE_CHARS])[0]
    raw_label = result["label"].lower()
    score = result["score"]

    if raw_label == "positive":
        label = "bullish"
    elif raw_label == "negative":
        label = "bearish"
    else:
        label = "neutral"

    return {"label": label, "score": score}
