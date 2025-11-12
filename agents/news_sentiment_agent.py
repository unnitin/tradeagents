"""Concrete agent that wraps the SentimentLLMStrategy."""

from __future__ import annotations

from agents.strategy_agent import StrategyAgent
from strategies import SentimentLLMStrategy


class NewsSentimentAgent(StrategyAgent):
    """
    Agent responsible for turning news headlines into directional sentiment.

    It expects the calling context to provide a dataframe via `context.news_data`
    with at least a `news_headline` column. When no news data is available the
    agent returns an empty signal payload but keeps metadata describing the
    configured thresholds so downstream systems can log diagnostics.
    """

    def __init__(
        self,
        sentiment_threshold: float = 0.3,
        name: str = "news_sentiment",
    ) -> None:
        strategy = SentimentLLMStrategy(sentiment_threshold=sentiment_threshold)
        super().__init__(
            name=name,
            role="news_sentiment",
            strategy=strategy,
            data_selector=lambda ctx: ctx.news_data,
            allow_empty_input=True,
        )

    def run(self, context):
        output = super().run(context)
        output.metadata.setdefault("sentiment_threshold", self.strategy.threshold)
        return output
