import pandas as pd
from strategies.base import Strategy
from utils import score_sentiment

class SentimentLLMStrategy(Strategy):
    def __init__(self, sentiment_threshold: float = 0.3):
        self.threshold = sentiment_threshold

    def generate_signals(self, news_df: pd.DataFrame) -> pd.Series:
        """
        Assumes a column 'news_headline' exists in news_df with daily/periodic news summaries.
        """
        signal = pd.Series(0, index=news_df.index)

        for idx, row in news_df.iterrows():
            headline = row.get("news_headline", "")
            if headline:
                sentiment_result = score_sentiment(headline)
                # Convert sentiment label to numeric score
                if sentiment_result['label'] == 'bullish':
                    score = sentiment_result['score']
                elif sentiment_result['label'] == 'bearish':
                    score = -sentiment_result['score']
                else:  # neutral
                    score = 0.0
                
                if score > self.threshold:
                    signal[idx] = 1
                elif score < -self.threshold:
                    signal[idx] = -1

        return signal
