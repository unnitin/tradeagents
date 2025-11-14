"""
Generic wrappers that turn Strategy instances into fully fledged agents.
TODO: @codex_agent - Highlight the purpose of this module more comprehensively - explain with examples what it should do and why it is needed.
"""

from __future__ import annotations

from typing import Callable, Optional

import pandas as pd

from agents.base import Agent, AgentContext, AgentError, AgentOutput
from strategies import Strategy


class StrategyAgent(Agent):
    """
    Thin adapter that lets any Strategy participate in the agent layer.

    By default it pulls price/indicator frames from `context.data['price_data']`
    but callers can override this through a custom `data_selector`.
    """

    def __init__(
        self,
        name: str,
        role: str,
        strategy: Strategy,
        data_key: str = "price_data",
        data_selector: Optional[Callable[[AgentContext], pd.DataFrame]] = None,
        allow_empty_input: bool = False,
    ) -> None:
        required = [] if data_selector else [data_key]
        super().__init__(name=name, role=role, required_keys=required)
        self.strategy = strategy
        self.data_key = data_key
        self.data_selector = data_selector
        self.allow_empty_input = allow_empty_input

    def _extract_input(self, context: AgentContext) -> Optional[pd.DataFrame]:
        """Resolve the dataframe that should be fed into the wrapped strategy."""
        if self.data_selector:
            frame = self.data_selector(context)
        else:
            frame = context.get(self.data_key)

        if frame is None:
            if self.allow_empty_input:
                return None
            raise AgentError(
                f"Agent '{self.name}' expected '{self.data_key}' in context data."
            )

        if not isinstance(frame, pd.DataFrame):
            raise AgentError(
                f"Agent '{self.name}' expected a pandas DataFrame for '{self.data_key}'."
            )

        return frame

    def run(self, context: AgentContext) -> AgentOutput:
        frame = self._extract_input(context)
        if frame is None or frame.empty:
            return AgentOutput(
                signals=None,
                reasoning="No data available for strategy execution.",
                metadata={"strategy": self.strategy.__class__.__name__},
            )

        if getattr(self.strategy, "filters", None):
            generator = getattr(self.strategy, "generate_signals_with_filters", None)
            if callable(generator):
                signals = generator(frame)
            else:
                signals = self.strategy.generate_signals(frame)
        else:
            signals = self.strategy.generate_signals(frame)

        return AgentOutput(
            signals=signals,
            metadata={"strategy": self.strategy.__class__.__name__},
        )

