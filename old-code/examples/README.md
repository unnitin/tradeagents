# Examples

The `examples/` directory contains runnable scripts that demonstrate how to stitch together the major modules—data ingestion, strategies, the composer, and the backtest engine. Each script mirrors a scenario from `spec.md` so you can experiment quickly or use them as integration tests.

## Script Guide

| Script | Scenario |
| --- | --- |
| `complete_workflow_example.py` | End‑to‑end flow: fetch data → engineer features → run a strategy → backtest → print metrics. |
| `strategy_composer_example.py` / `composer_backtest_example.py` | Show how to configure the `StrategyComposer`, execute ensemble combinations, and evaluate them. |
| `backtest_example.py` / `backtest_comprehensive_example.py` | Different levels of backtesting detail, including filters, commission settings, and benchmark comparison. |
| `filter_config_example.py` / `config_example.py` | Demonstrate how YAML-driven configs (filters + backtest settings) instantiate runtime objects. |
| `advanced_filter_example.py` | Focused look at chaining `StockFilter`, `TimeFilter`, and `LiquidityFilter`. |
| `politician_tracking_example.py` | Highlights the alternative-data strategies that follow congressional trades. |

## How to Run

```bash
cd examples
python3 complete_workflow_example.py
```

Feel free to copy these scripts as templates when wiring the modules into a CLI, API, or notebook.

