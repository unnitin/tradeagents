"""Risk overlay agent that enforces guardrails on raw signals."""

from __future__ import annotations

from typing import Optional, Tuple

import pandas as pd

from agents.base import Agent, AgentContext, AgentError, AgentOutput


class RiskManagementAgent(Agent):
    """
    Applies coarse risk constraints (position caps, volatility filters, drawdown stops)
    to the outputs of other agents before they reach execution/backtests.
    """

    def __init__(
        self,
        signals_key: str = "candidate_signals",
        max_positions: Optional[int] = 10,
        max_position_size: Optional[float] = 1.0,
        volatility_column: Optional[str] = None,
        volatility_threshold: Optional[float] = None,
        max_drawdown: Optional[float] = None,
        name: str = "risk_manager",
    ) -> None:
        super().__init__(name=name, role="risk", required_keys=[signals_key])
        self.signals_key = signals_key
        self.max_positions = max_positions
        self.max_position_size = max_position_size
        self.volatility_column = volatility_column
        self.volatility_threshold = volatility_threshold
        self.max_drawdown = max_drawdown

    def run(self, context: AgentContext) -> AgentOutput:
        raw_signals = context.get(self.signals_key)
        frame, original_type = self._coerce_to_frame(raw_signals)
        if frame.empty:
            return AgentOutput(reasoning="No candidate signals to risk-adjust.")

        enforcement_notes = []

        if self.max_positions is not None:
            if self._enforce_position_cap(frame):
                enforcement_notes.append(f"max_positions={self.max_positions}")

        if self.max_position_size is not None:
            threshold = abs(self.max_position_size)
            if (frame.abs() > threshold).any().any():
                frame.clip(
                    lower=-threshold,
                    upper=threshold,
                    inplace=True,
                )
                enforcement_notes.append(f"max_position_size=±{threshold:.2f}")

        indicators = context.get("risk_indicators")
        if (
            self.volatility_column
            and self.volatility_threshold is not None
            and isinstance(indicators, pd.DataFrame)
        ):
            if self.volatility_column in indicators.columns:
                high_vol_index = indicators.index[
                    indicators[self.volatility_column] > self.volatility_threshold
                ]
                clipped_index = frame.index.intersection(high_vol_index)
                if len(clipped_index) > 0:
                    frame.loc[clipped_index] = 0
                    enforcement_notes.append(
                        f"{self.volatility_column}>{self.volatility_threshold}"
                    )

        current_drawdown = context.metadata.get("current_drawdown")
        if (
            self.max_drawdown is not None
            and isinstance(current_drawdown, (int, float))
            and current_drawdown >= self.max_drawdown
        ):
            frame.loc[:, :] = 0
            enforcement_notes.append(
                f"drawdown_stop={current_drawdown:.2%}/{self.max_drawdown:.2%}"
            )

        adjusted = self._restore_type(frame, original_type, raw_signals)
        reasoning = (
            "Applied risk constraints: " + ", ".join(enforcement_notes)
            if enforcement_notes
            else "Risk manager active but no constraints triggered."
        )

        return AgentOutput(
            signals=adjusted,
            metadata={"enforcements": enforcement_notes},
            reasoning=reasoning,
        )

    def _coerce_to_frame(
        self, payload
    ) -> Tuple[pd.DataFrame, str]:
        """Normalize various signal containers into a dataframe representation."""
        if isinstance(payload, pd.DataFrame):
            return payload.copy(), "dataframe"
        if isinstance(payload, pd.Series):
            return payload.to_frame(name="signal"), "series"
        if isinstance(payload, dict):
            return pd.DataFrame(payload).copy(), "dict"
        raise AgentError(
            f"Risk agent '{self.name}' expected pandas objects, got {type(payload)}"
        )

    def _restore_type(self, frame: pd.DataFrame, payload_type: str, original):
        """Convert the dataframe back to the shape it arrived in."""
        if payload_type == "dataframe":
            return frame
        if payload_type == "series":
            column = frame.columns[0]
            return frame[column]
        if payload_type == "dict":
            return {col: frame[col] for col in frame.columns}
        raise AgentError(f"Unknown payload type '{payload_type}' in risk agent.")

    def _enforce_position_cap(self, frame: pd.DataFrame) -> bool:
        """Limit number of concurrent non-zero signals per timestamp."""
        if self.max_positions is None:
            return False

        applied = False
        for idx in frame.index:
            row = frame.loc[idx]
            non_zero = row[row != 0]
            if len(non_zero) <= self.max_positions:
                continue

            keep = (
                non_zero.abs()
                .sort_values(ascending=False)
                .head(self.max_positions)
                .index
            )
            drop = [col for col in non_zero.index if col not in keep]
            frame.loc[idx, drop] = 0
            applied = True

        return applied
