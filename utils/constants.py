# Configuration for LLM/NLP tools used in sentiment analysis

# Model & Tokenizer
FINBERT_MODEL_NAME = "ProsusAI/finbert"
FINBERT_TOKENIZER = "ProsusAI/finbert"

# Input truncation (maximum tokenized string length)
SENTIMENT_TRUNCATE_CHARS = 512

# Sentiment interpretation threshold (optional global default)
DEFAULT_SENTIMENT_THRESHOLD = 0.6
