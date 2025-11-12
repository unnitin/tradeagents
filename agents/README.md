## Agents Module

The `agents/` package turns AstraQuant’s autonomous workflow from the spec into code. It provides shared plumbing (`Agent`, `AgentContext`, `AgentOutput`) plus the first concrete roles:

| Agent | Responsibility | Key Inputs | Output |
| --- | --- | --- | --- |
| `NewsSentimentAgent` | Score headlines with FinBERT/LLM sentiment and emit directional signals. | `context.news_data` dataframe with `news_headline` column. | Bullish/bearish series plus metadata about thresholds. |
| `TechnicalCompositeAgent` | Portfolio-manager role that asks `StrategyComposer` to run weighted/voting ensembles. | `context.price_data` (OHLCV + features) and `config/strategies.yaml`. | Combined technical signal series with combination metadata. |
| `RiskManagementAgent` | Safety layer that caps concurrent trades, draws down leverage during stress, and zeros signals when volatility spikes. | `context.data['candidate_signals']` plus optional `context.data['risk_indicators']` and `context.metadata['current_drawdown']`. | Adjusted signal frame/series + audit trail of enforcement notes. |

### Core API

- `Agent`: Abstract base class. Implements validation, metadata decoration, and a callable interface.
- `AgentContext`: Shared data capsule (`data`, `preferences`, `metadata`) with helpers such as `.price_data`, `.news_data`, `.require(...)`.
- `AgentOutput`: Normalised response containing signals, optional confidence, textual reasoning, and diagnostics.
- `StrategyAgent`: Adapter that lets any class from `strategies/` become an agent by specifying which dataframe it should read from the context.
- `registry`: Simple factory registry so other modules (API layer, CLI, orchestration scripts) can request agents by name instead of hard-coding imports.

### Key Functionality To Build Next

1. **Expanded Agent Set** – Implement analyst agents for politician trades, social sentiment, macro regimes, and the future “debate” arbiter mentioned in `spec.md`.
2. **Task Graphs** – Allow agents to pass intermediate artifacts (research notes, raw signals) to each other before the composer consumes them.
3. **Preference-Aware Behaviour** – Enrich `AgentContext.preferences` with questionnaire data so each agent can tailor aggressiveness, asset universe, or time horizon per user.
4. **Learning / Feedback Loop** – Persist `AgentOutput.metadata` snapshots so backtests and live monitoring can feed outcomes back into agent configs (e.g., auto-downgrade an agent whose recent Sharpe fell below a threshold).
5. **Observability Hooks** – Emit structured logs or traces whenever an agent enforces a guardrail, fetches alternative data, or changes conviction. This supports the explainability requirements outlined in the spec’s UX section.

### Usage Sketch

```python
from agents import AgentContext, registry
import pandas as pd

context = AgentContext(
    data={
        "price_data": price_frame,      # e.g., OHLCV + indicators
        "news_data": news_frame,        # columns: date, news_headline
        "candidate_signals": candidate, # pd.DataFrame or dict of Series
        "risk_indicators": risk_frame,  # optional ATR/VIX readings
    },
    preferences={"risk": "balanced"},
    metadata={"current_drawdown": 0.04},
)

technical_agent = registry.create("technical_composite", combination_name="technical_ensemble")
sentiment_agent = registry.create("news_sentiment")
risk_agent = registry.create("risk_manager", volatility_column="ATR14", volatility_threshold=5.0)

technical_signals = technical_agent(context)
sentiment_signals = sentiment_agent(context)
risk_adjusted = risk_agent(
    context.with_updates(candidate_signals={
        "technical": technical_signals.signals,
        "sentiment": sentiment_signals.signals,
    })
)
```

This README will evolve alongside the module as more autonomous behaviour lands (LLM debate loops, reinforcement learning optimizers, etc.). For now it captures the MVP functionality and the next objectives so contributors know where to plug in.

