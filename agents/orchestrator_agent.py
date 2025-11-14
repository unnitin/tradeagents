"""Agent that orchestrates composer runs and immediate backtests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

from agents.base import Agent, AgentContext, AgentError, AgentOutput
from backtest import BacktestResults, create_backtest_engine
from composer.strategy_composer import StrategyComposer
from config.backtest_config import BacktestConfigManager


@dataclass
class NewsSummary:
    headline_count: int
    unique_symbols: int


class StrategyOrchestratorAgent(Agent):
    """
    High-level orchestrator that evaluates market context, generates signals via
    the StrategyComposer, and immediately backtests the chosen combination.

    The agent expects price data in the context and optionally uses metadata
    inputs such as symbols, start/end dates, or alternative combination names.
    """

    def __init__(
        self,
        combination_name: str = "technical_ensemble",
        config_path: str = "config/strategies.yaml",
        backtest_config_name: str = "default",
        name: str = "strategy_orchestrator",
    ) -> None:
        super().__init__(name=name, role="orchestrator", required_keys=["price_data"])
        self.default_combination = combination_name
        self.config_path = config_path
        self.backtest_config_name = backtest_config_name
        self.composer = StrategyComposer(config_path=config_path)
        self.composer.register_strategies()
        self.config_manager = BacktestConfigManager()

    def run(self, context: AgentContext) -> AgentOutput:
        price_data = context.price_data
        if price_data is None or price_data.empty:
            return AgentOutput(reasoning="No price data provided for orchestration.")

        combination = self._select_combination(context)

        try:
            signals = self.composer.execute_combination(combination, price_data)
            combo_config = self.composer.get_combination_info(combination)
        except ValueError as exc:
            raise AgentError(str(exc)) from exc

        news_summary = self._summarize_news(context.news_data)
        indicator_summary = self._summarize_indicators(price_data)

        backtest_metadata: Dict[str, float] | Dict[str, str] = {
            "status": "skipped",
            "reason": "Insufficient metadata for backtest.",
        }
        symbols, date_range = self._resolve_backtest_inputs(context, price_data)
        if symbols and date_range:
            config_name = context.metadata.get(
                "backtest_config", self.backtest_config_name
            )
            backtest_metadata = self._run_backtest(
                combination,
                symbols,
                date_range,
                context.metadata.get("data_interval", "1d"),
                config_name,
            )

        reasoning = self._craft_reasoning(
            combination=combination,
            symbols=symbols or [],
            date_range=date_range,
            backtest_info=backtest_metadata,
            news_summary=news_summary,
        )

        metadata = {
            "combination": combination,
            "strategies": combo_config.get("strategies", []),
            "method": combo_config.get("method"),
            "indicator_summary": indicator_summary,
            "news_summary": news_summary.__dict__ if news_summary else None,
            "backtest": backtest_metadata,
            "symbols": symbols,
            "date_range": date_range,
        }

        return AgentOutput(signals=signals, reasoning=reasoning, metadata=metadata)

    def _select_combination(self, context: AgentContext) -> str:
        return (
            context.metadata.get("combination_name")
            or context.preferences.get("combination_name")
            or self.default_combination
        )

    def _resolve_backtest_inputs(
        self, context: AgentContext, price_data: pd.DataFrame
    ) -> Tuple[Optional[List[str]], Optional[Dict[str, str]]]:
        symbols: Optional[List[str]] = None
        if "symbol" in price_data.columns:
            unique = price_data["symbol"].dropna().unique().tolist()
            symbols = [str(sym) for sym in unique if isinstance(sym, (str, int))]
        if not symbols:
            meta_symbols = context.metadata.get("symbols") or context.data.get("symbols")
            if isinstance(meta_symbols, str):
                symbols = [meta_symbols]
            elif isinstance(meta_symbols, list):
                symbols = meta_symbols

        date_range: Optional[Dict[str, str]] = None
        date_series: Optional[pd.Series] = None
        for candidate in ("date", "timestamp", "datetime"):
            if candidate in price_data.columns:
                date_series = pd.to_datetime(price_data[candidate], errors="coerce")
                break
        if date_series is None and isinstance(price_data.index, pd.DatetimeIndex):
            date_series = price_data.index.to_series()

        if date_series is not None and not date_series.empty:
            date_range = {
                "start": date_series.min().date().isoformat(),
                "end": date_series.max().date().isoformat(),
            }
        else:
            meta_start = context.metadata.get("start_date")
            meta_end = context.metadata.get("end_date")
            if meta_start and meta_end:
                date_range = {"start": meta_start, "end": meta_end}

        return symbols, date_range

    def _run_backtest(
        self,
        combination: str,
        symbols: List[str],
        date_range: Dict[str, str],
        interval: str,
        config_name: str,
    ) -> Dict[str, float | str]:
        try:
            config = self.config_manager.get_config(config_name)
        except ValueError as exc:
            return {"status": "error", "reason": str(exc)}

        engine = create_backtest_engine(config)
        try:
            results = engine.run_composer_backtest(
                combination_name=combination,
                symbols=symbols,
                start_date=date_range["start"],
                end_date=date_range["end"],
                composer=self.composer,
                data_interval=interval,
            )
        except Exception as exc:  # pragma: no cover - defensive
            return {"status": "error", "reason": str(exc)}

        return self._summarize_metrics(results)

    def _summarize_metrics(self, results: BacktestResults) -> Dict[str, float | str]:
        metrics = results.metrics
        return {
            "status": "ok",
            "total_return": metrics.total_return,
            "annualized_return": metrics.annualized_return,
            "sharpe_ratio": metrics.sharpe_ratio,
            "max_drawdown": metrics.max_drawdown,
            "win_rate": metrics.win_rate,
            "total_trades": metrics.total_trades,
            "backtest_id": results.backtest_id,
        }

    def _summarize_news(self, news_df: Optional[pd.DataFrame]) -> Optional[NewsSummary]:
        if news_df is None or news_df.empty:
            return None
        if "symbol" in news_df.columns:
            unique_symbols = news_df["symbol"].dropna().nunique()
        elif "symbols" in news_df.columns:
            exploded = news_df["symbols"].explode()
            unique_symbols = exploded.dropna().nunique()
        else:
            unique_symbols = 0
        return NewsSummary(headline_count=len(news_df), unique_symbols=unique_symbols)

    def _summarize_indicators(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        indicators: Dict[str, List[str]] = {}
        columns = df.columns
        buckets = {
            "trend": [col for col in columns if col.startswith(("sma_", "ema_"))],
            "momentum": [col for col in columns if col.startswith("rsi_") or "macd" in col],
            "volatility": [col for col in columns if col.startswith(("atr_", "bb_"))],
        }
        for bucket, cols in buckets.items():
            if cols:
                indicators[bucket] = cols
        return indicators

    def _craft_reasoning(
        self,
        combination: str,
        symbols: List[str],
        date_range: Optional[Dict[str, str]],
        backtest_info: Dict[str, float | str],
        news_summary: Optional[NewsSummary],
    ) -> str:
        parts = [
            f"Orchestrated combination '{combination}'",
        ]
        if symbols:
            parts.append(f"across {len(symbols)} symbol(s)")
        if date_range:
            parts.append(f"for {date_range['start']}→{date_range['end']}.")
        else:
            parts.append("using supplied price snapshot.")

        if backtest_info.get("status") == "ok":
            parts.append(
                "Backtest: "
                f"return {backtest_info['total_return']:.2%}, "
                f"Sharpe {backtest_info['sharpe_ratio']:.2f}, "
                f"max drawdown {backtest_info['max_drawdown']:.2%}."
            )
        else:
            reason = backtest_info.get("reason", "unknown issue")
            parts.append(f"Backtest unavailable ({reason}).")

        if news_summary:
            parts.append(
                f"News context: {news_summary.headline_count} headlines over "
                f"{news_summary.unique_symbols} symbol(s)."
            )

        return " ".join(parts)
