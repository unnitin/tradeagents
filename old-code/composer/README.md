# Strategy Composer

`composer/` houses the portfolio-manager logic that fuses signals from multiple agents/strategies. It is the implementation of the “Strategy Composer (Portfolio Manager Agent)” described in `spec.md`.

## What It Does

- Reads `config/strategies.yaml`, instantiates all enabled strategies, and tracks whether each is a directional strategy or a filter.
- Applies per-strategy filter configs (liquidity, time, symbol lists) using the `filters/` package.
- Combines signals through flexible methods: `single`, `majority_vote`, `weighted_average`, or `unanimous`.
- Supports both data-level filters (pre-filtering the price frame) and legacy filter strategies for backward compatibility.
- Exposes convenience helpers (`create_composer`, `get_signals`) so backtests, APIs, or agents can request ensembles on demand.

## Key Files

| File | Purpose |
| --- | --- |
| `strategy_composer.py` | Implements `StrategyComposer`, combination helpers, and module-level convenience functions. |
| `__init__.py` | Re-exports `StrategyComposer`, `create_composer`, and `get_signals` for ergonomic imports. |

## Quick Start

```python
import pandas as pd
from composer import create_composer

price_df = pd.read_parquet("data/aapl_features.parquet")
composer = create_composer("config/strategies.yaml")

signals = composer.execute_combination("technical_ensemble", price_df)
```

### Weights & Methods

```yaml
combinations:
  technical_ensemble:
    strategies: [sma_crossover, rsi_reversion, macd_cross, bollinger_bounce]
    method: majority_vote
    filters:
      - atr_filter

  hybrid_political:
    strategies: [sma_crossover, rsi_reversion, pelosi_tracking, congress_momentum]
    method: weighted_average
    weights:
      sma_crossover: 0.3
      rsi_reversion: 0.2
      pelosi_tracking: 0.3
      congress_momentum: 0.2
```

## Data-Level Filtering

Each combination can embed a `filter_config` block that maps directly to `config/filter_config.py`:

```yaml
filter_config:
  logic: AND
  stock_filter:
    min_volume: 2_000_000
    min_price: 15
  time_filter:
    exclude_market_holidays: true
    min_trading_days: 60
```

The composer builds these filters, applies them to the incoming dataframe, and passes the filtered view to every participating strategy.

## Integration with Agents

The `agents/technical_agent.py` module wraps the composer so ensemble logic can be triggered within the multi-agent framework. The composer therefore:

1. Acts as a reusable service for any orchestrator (agents, CLI, API).
2. Provides metadata (`get_combination_info`) that surfaces in UX or logging layers for explainability.

Keep `strategies.yaml` up to date and the composer will automatically reflect the desired behaviour without new Python glue.
