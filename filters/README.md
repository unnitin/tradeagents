# Filters Module

This package centralizes every data-level guardrail used by strategies, agents, and the backtest engine. It implements reusable filters that screen symbols, timestamps, and liquidity conditions before any trade logic fires—mirroring the guardrails called out in `spec.md`.

## Key Responsibilities

| File | Purpose |
| --- | --- |
| `core.py` | Defines `BaseFilter` plus concrete `StockFilter`, `TimeFilter`, `LiquidityFilter`, and `CompositeFilter`. |
| `__init__.py` | Convenience exports and helper constructors (`create_*_filter`, preset builders such as `create_day_trading_filter`). |

### Supported Filters

- **StockFilter** – Screens securities by price, volume, market cap, volatility, and inclusion/exclusion lists.
- **TimeFilter** – Excludes market holidays, earnings windows, or arbitrary date/time ranges.
- **LiquidityFilter** – Enforces minimum average volume, dollar volume, or maximum bid/ask spread.
- **CompositeFilter** – Chains any mix of filters using AND/OR logic, so the composer/backtest can treat them as a single object.

## Quick Start

```python
from filters import StockFilter, TimeFilter, LiquidityFilter, CompositeFilter

stock_filter = StockFilter(min_volume=2_000_000, min_price=15.0, max_volatility=0.04)
time_filter = TimeFilter(exclude_market_holidays=True, min_trading_days=60)
liquidity_filter = LiquidityFilter(min_avg_volume=3_000_000, max_bid_ask_spread=0.001)

universe_filter = CompositeFilter(
    [stock_filter, time_filter, liquidity_filter],
    logic="AND",
)
filtered_df = universe_filter.apply_filter(price_frame)
```

## Presets and Config Integration

- `filters/__init__.py` exposes helpers such as `create_conservative_filter()` and ties directly into `config/filter_config.py`, so YAML entries can instantiate the same objects without hand-written code.
- Strategy classes (via `Strategy.set_filters`) and the `StrategyComposer` both rely on these filters to respect user preferences (risk tolerance, sector exclusions, etc.) and to satisfy the safety guardrails detailed in the specification.

Use this module whenever you need a consistent rule for “which symbols/periods are even eligible” before applying higher-level logic.

