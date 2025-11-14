"""
Core building blocks for agentified strategy workflows.

This module defines the shared context, output envelope, and abstract Agent
interface that concrete role implementations can inherit from. It keeps the
agents layer decoupled from specific strategies or backtest plumbing while
still giving them a consistent contract for inputs/outputs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import pandas as pd


class AgentError(RuntimeError):
    """Raised when an agent cannot complete its task because of invalid input."""


@dataclass
class AgentContext:
    """
    Shared context container passed to every agent invocation.

    The context is intentionally flexible; callers can drop arbitrary frames
    or metadata into the `data` dictionary while relying on the convenience
    accessors for common resources like price history or news sentiment.
    """

    data: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a data payload by key."""
        return self.data.get(key, default)

    def require(self, *keys: str) -> Tuple[Any, ...]:
        """
        Retrieve several required keys, raising if any are missing.

        Returns:
            tuple[Any, ...]: Values aligned with the requested keys.
        """
        missing = [key for key in keys if self.get(key) is None]
        if missing:
            raise AgentError(f"Missing required context keys: {missing}")
        return tuple(self.get(key) for key in keys)

    def with_updates(self, **new_data: Any) -> "AgentContext":
        """Return a shallow copy with updated data entries."""
        merged = {**self.data, **new_data}
        return AgentContext(
            data=merged,
            preferences=self.preferences.copy(),
            metadata=self.metadata.copy(),
        )

    @property
    def price_data(self) -> Optional[pd.DataFrame]:
        """Shorthand accessor for unified price/indicator tables."""
        value = self.data.get("price_data")
        return value if isinstance(value, pd.DataFrame) else None

    @property
    def news_data(self) -> Optional[pd.DataFrame]:
        """Shorthand accessor for news or headline level datasets."""
        value = self.data.get("news_data")
        return value if isinstance(value, pd.DataFrame) else None

    @property
    def politician_trades(self) -> Optional[pd.DataFrame]:
        """Accessor for politician/alternative trade disclosures."""
        value = self.data.get("politician_trades")
        return value if isinstance(value, pd.DataFrame) else None


@dataclass
class AgentOutput:
    """
    Standardized output envelope returned by every agent.

    Attributes:
        signals: Time series or panel of trading signals produced.
        score: Optional confidence score in [-1, 1] for downstream weighting.
        reasoning: Natural language explanation for transparency/UX layers.
        metadata: Arbitrary diagnostic information (latencies, configs, etc.).
    """

    signals: Optional[Union[pd.Series, pd.DataFrame]] = None
    score: Optional[float] = None
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_empty(self) -> bool:
        """Return True if no signal payload is attached."""
        if self.signals is None:
            return True
        if isinstance(self.signals, pd.DataFrame):
            return self.signals.empty
        return self.signals.empty  # Series case


class Agent(ABC):
    """
    Abstract base class for every agent role in the system.

    Subclasses implement `run` to translate an AgentContext into an
    AgentOutput. The base class handles validation, metadata decoration,
    and a callable interface for ergonomic use inside pipelines.
    """

    def __init__(
        self,
        name: str,
        role: str,
        required_keys: Optional[Iterable[str]] = None,
    ) -> None:
        self.name = name
        self.role = role
        self.required_keys: List[str] = list(required_keys or [])

    def __call__(self, context: Optional[AgentContext] = None) -> AgentOutput:
        """Allow agents to be invoked like callables."""
        context = context or AgentContext()
        self._validate_context(context)
        output = self.run(context)
        if output is None:
            output = AgentOutput()
        output.metadata.setdefault("agent_name", self.name)
        output.metadata.setdefault("agent_role", self.role)
        return output

    def _validate_context(self, context: AgentContext) -> None:
        """Ensure required context entries exist before execution."""
        missing = [key for key in self.required_keys if context.get(key) is None]
        if missing:
            raise AgentError(
                f"Agent '{self.name}' missing required context keys: {missing}"
            )

    @abstractmethod
    def run(self, context: AgentContext) -> AgentOutput:
        """Execute agent logic and return signals or insights."""
        raise NotImplementedError
