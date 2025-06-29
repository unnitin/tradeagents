import pandas as pd
from strategies.base import Strategy
from utils.sentiment_engine import score_sentiment

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
            score = score_sentiment(headline)
            if score > self.threshold:
                signal[idx] = 1
            elif score < -self.threshold:
                signal[idx] = -1

        return signal
