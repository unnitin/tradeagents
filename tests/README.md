# Tests

The `tests/` package keeps unit tests and integration tests organised so regressions are caught before strategies go live.

## Layout

```
tests/
├── unit_test/          # Fast tests for pure functions (indicators, filters, utilities)
├── integration/        # Scenario tests that stitch modules together (data → strategy → backtest)
├── test_backtest_runner.py
└── run_tests.py        # Helper script to execute the full suite via unittest discovery
```

## Running the Suite

```bash
export ASTRAQUANT_SENTIMENT_MODE=mock  # skip FinBERT downloads during tests
python3 -m unittest discover -s tests -t .
# or
python3 tests/run_tests.py
```

## Coverage Goals

- Ensure every strategy and agent has dedicated unit tests.
- Keep regression tests for the `StrategyComposer` and `BacktestEngine` so future config changes remain safe.
- Mirror the safety guardrails from the specification (position limits, drawdown stops) with assertions inside integration cases.

Add new tests next to the code they exercise and update this README if new suites or tooling appear.
