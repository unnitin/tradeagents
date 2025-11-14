# AstraQuant

AI-augmented research platform for designing, evaluating, and explaining trading strategies across equities and top‑10 crypto. Agents consume multi-source data (prices, politician trades, news sentiment), debate signals through the strategy composer, and validate outcomes with a high-fidelity backtest engine.

---

## Why It Matters
- **Context-aware signals** – Combine structured indicators with unstructured sentiment and alternative data.
- **Agent-first design** – Every role (news, technical, risk) implements a shared `AgentContext`/`AgentOutput` contract, so orchestration is composable.
- **Config-driven** – Strategies, ensembles, and risk presets live in YAML, keeping iteration fast.
- **Explainable results** – Metadata from agents/backtests can be surfaced directly to UX layers for transparent decisions.

---

## Core Modules

| Module | Description |
| --- | --- |
| `data/` | Fetch Yahoo Finance OHLCV, Quiver politician trades, and news headlines; add indicators through a pipeline. |
| `strategies/` | Technical, sentiment, and alternative-data strategies that all inherit from `Strategy`. |
| `composer/` | Portfolio-manager logic that blends strategy outputs via voting, weighting, or unanimity, honoring filter configs. |
| `agents/` | Runtime agent layer (news sentiment, technical ensemble, risk manager) built on a shared base interface + registry. |
| `filters/` | Stock/time/liquidity filters plus composite logic used by strategies, composer, and backtests. |
| `backtest/` | Simulation engine with portfolio accounting, guardrails, and rich metrics (Sharpe, drawdown, VaR, etc.). |
| `config/` | YAML definitions for strategies, combinations, filters, and backtest presets, plus loaders/validators. |

Full documentation for each directory lives in its local `README.md`.

---

## Quick Start

```bash
git clone git@github.com:unnitin/trade.git
cd trade
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Run a sample workflow:

```python
from agents import AgentContext, registry
from data.fetch_data import DataFetcher

fetcher = DataFetcher()
price_df = fetcher.get_stock_data("AAPL", interval="1d")
news_df = fetcher.get_news_data(symbols=["AAPL"])

context = AgentContext(data={"price_data": price_df, "news_data": news_df})
technical_agent = registry.create("technical_composite")
sentiment_agent = registry.create("news_sentiment")

tech_output = technical_agent(context)
sent_output = sentiment_agent(context)
```

Backtest an ensemble:

```python
from backtest import create_backtest_engine
from composer import create_composer

engine = create_backtest_engine()
composer = create_composer("config/strategies.yaml")

signals = composer.execute_combination("technical_ensemble", price_df)
results = engine.run_signal_backtest(signals, price_df)
print(results.metrics.sharpe_ratio)
```

---

## Agents Layer

- **StrategyAgent** – Wraps any `Strategy` class so it plugs into the agent runtime.
- **NewsSentimentAgent** – Scores headlines via FinBERT (through `SentimentLLMStrategy`) to produce bullish/bearish calls.
- **TechnicalCompositeAgent** – Delegates to `StrategyComposer` to emit ensemble signals.
- **RiskManagementAgent** – Applies max positions, position size caps, volatility gates, and drawdown stops before execution.

Use `agents.registry` to construct agents by name when wiring APIs or workflows.

---

## Directory Map

```
agents/         Agent interfaces + concrete roles
backtest/       Engine, portfolio, metrics, results management
composer/       StrategyComposer orchestrator
config/         YAML configs + loaders
data/           Fetchers, indicators, news ingestion
examples/       End-to-end workflow demos
filters/        Stock/time/liquidity filters
strategies/     Technical + alternative-data strategies
tests/          Unit + integration suites
utils/          Sentiment engine and shared helpers
```

---

## Roadmap (Excerpt)
1. **Agent debate loop** – Enable multi-agent reasoning (bull vs bear arguments) before composing signals.
2. **Preference-aware agents** – Feed questionnaire results into `AgentContext.preferences` to personalize tactics.
3. **Reinforcement learning** – Explore automatic parameter tuning using backtest feedback loops.
4. **API surface** – Expose agent/backtest endpoints via FastAPI for web/mobile consumption.

Contributions welcome—open an issue or PR with context on data sources, risk constraints, or agent behaviors.

