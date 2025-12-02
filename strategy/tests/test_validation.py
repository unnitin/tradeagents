from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.services.validation import validate_strategy_spec


def test_sma_crossover_example_is_valid() -> None:
    spec = {
        "schema_version": "1.0",
        "timeframe": "1d",
        "universe": {"type": "preset", "value": "SP500"},
        "entry": {
            "logic": "and",
            "conditions": [
                {
                    "type": "indicator_cross",
                    "fast": {"indicator": "SMA", "params": {"window": 50}},
                    "slow": {"indicator": "SMA", "params": {"window": 200}},
                    "direction": "up",
                }
            ],
        },
        "exit": {
            "logic": "and",
            "conditions": [
                {
                    "type": "indicator_cross",
                    "fast": {"indicator": "SMA", "params": {"window": 50}},
                    "slow": {"indicator": "SMA", "params": {"window": 200}},
                    "direction": "down",
                }
            ],
        },
        "position_sizing": {"mode": "fixed_fraction", "fraction": 0.1, "max_positions": 10},
    }
    assert validate_strategy_spec(spec)[0]


def test_invalid_indicator_compare_surface_errors() -> None:
    spec = {
        "entry": {
            "logic": "and",
            "conditions": [
                {
                    "type": "indicator_compare",
                    "left": {"source": "constant", "value": 1},
                    "operator": "??",
                    "right": {"source": "constant", "value": "bad"},
                }
            ],
        }
    }
    valid, errors = validate_strategy_spec(spec)
    assert not valid
    assert any("left" in err["path"] for err in errors)
    assert any("operator" in err["path"] for err in errors)
