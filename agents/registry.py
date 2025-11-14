"""Lightweight registry for dynamically constructing agents by name."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

from agents.base import Agent
from agents.news_sentiment_agent import NewsSentimentAgent
from agents.orchestrator_agent import StrategyOrchestratorAgent
from agents.risk_agent import RiskManagementAgent
from agents.technical_agent import TechnicalCompositeAgent


class AgentRegistry:
    """Keeps track of available agent factories for dynamic instantiation."""

    def __init__(self) -> None:
        self._factories: Dict[str, Callable[..., Agent]] = {}

    def register(self, name: str, factory: Callable[..., Agent]) -> None:
        if name in self._factories:
            raise ValueError(f"Agent '{name}' already registered.")
        self._factories[name] = factory

    def create(self, name: str, **kwargs) -> Agent:
        if name not in self._factories:
            raise KeyError(f"Agent '{name}' not found in registry.")
        return self._factories[name](**kwargs)

    def available(self) -> List[str]:
        return sorted(self._factories.keys())


# Global registry instance seeded with the core agents wiring
registry = AgentRegistry()
registry.register("news_sentiment", lambda **params: NewsSentimentAgent(**params))
registry.register(
    "technical_composite", lambda **params: TechnicalCompositeAgent(**params)
)
registry.register("risk_manager", lambda **params: RiskManagementAgent(**params))
registry.register(
    "strategy_orchestrator", lambda **params: StrategyOrchestratorAgent(**params)
)
