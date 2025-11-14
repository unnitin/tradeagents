"""Agents that orchestrate technical ensembles via the StrategyComposer."""

from __future__ import annotations

from typing import Optional

import pandas as pd

from agents.base import Agent, AgentContext, AgentError, AgentOutput
from composer.strategy_composer import StrategyComposer


class TechnicalCompositeAgent(Agent):
    """
    Portfolio-manager style agent that delegates to StrategyComposer.

    It loads the configured combination (defaults to `technical_ensemble`) and
    keeps the output in the standard AgentOutput envelope so downstream risk
    agents or backtests can treat it like any other producer.
    """

    def __init__(
        self,
        combination_name: str = "technical_ensemble",
        config_path: str = "config/strategies.yaml",
        composer: Optional[StrategyComposer] = None,
        name: str = "technical_composite",
    ) -> None:
        super().__init__(name=name, role="technical", required_keys=["price_data"])
        self.combination_name = combination_name
        self.composer = composer or StrategyComposer(config_path=config_path)
        # Pre-register to avoid surprises at runtime.
        self.composer.register_strategies()

    def run(self, context: AgentContext) -> AgentOutput:
        price_data = context.price_data
        if price_data is None or price_data.empty:
            return AgentOutput(
                reasoning="Price data not available for technical composite agent.",
            )

        try:
            signals = self.composer.execute_combination(
                self.combination_name,
                price_data,
            )
            combo_config = self.composer.get_combination_info(self.combination_name)
        except ValueError as exc:
            raise AgentError(str(exc)) from exc

        metadata = {
            "combination": self.combination_name,
            "strategies": combo_config.get("strategies", []),
            "method": combo_config.get("method"),
        }

        return AgentOutput(signals=signals, metadata=metadata)

