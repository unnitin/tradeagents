from transformers import pipeline
from utils.constants import (
    FINBERT_MODEL_NAME,
    FINBERT_TOKENIZER,
    SENTIMENT_TRUNCATE_CHARS,
)

# Initialize model from constants
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=FINBERT_MODEL_NAME,
    tokenizer=FINBERT_TOKENIZER
)

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
        return {'label': 'neutral', 'score': 0.0}

    result = sentiment_pipeline(text[:SENTIMENT_TRUNCATE_CHARS])[0]
    raw_label = result['label'].lower()
    score = result['score']

    if raw_label == 'positive':
        label = 'bullish'
    elif raw_label == 'negative':
        label = 'bearish'
    else:
        label = 'neutral'

    return {'label': label, 'score': score}
