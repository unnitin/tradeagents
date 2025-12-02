from __future__ import annotations

from typing import Dict, List

import pytest

from strategy.services.registry import StrategyRegistry, StrategySpecError
from strategy.services.validation import validate_strategy_spec
from strategy.store import StrategyRepository


SMA_CROSSOVER_SPEC: Dict[str, object] = {
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

RSI_MEAN_REVERSION_SPEC: Dict[str, object] = {
    "schema_version": "1.0",
    "timeframe": "1d",
    "universe": {"type": "preset", "value": "SP500"},
    "entry": {
        "logic": "and",
        "conditions": [
            {
                "type": "indicator_compare",
                "left": {"source": "indicator", "indicator": "RSI", "params": {"window": 14}, "field": "value"},
                "operator": "<",
                "right": {"source": "constant", "value": 30},
            }
        ],
    },
    "exit": {
        "logic": "and",
        "conditions": [
            {
                "type": "indicator_compare",
                "left": {"source": "indicator", "indicator": "RSI", "params": {"window": 14}, "field": "value"},
                "operator": ">",
                "right": {"source": "constant", "value": 50},
            }
        ],
    },
    "position_sizing": {"mode": "fixed_fraction", "fraction": 0.1, "max_positions": 5},
}

TREND_NEWS_SPEC: Dict[str, object] = {
    "schema_version": "1.0",
    "timeframe": "1d",
    "universe": {"type": "preset", "value": "SP500"},
    "entry": {
        "logic": "and",
        "conditions": [
            {
                "type": "indicator_compare",
                "left": {"source": "indicator", "indicator": "SMA", "params": {"window": 50}, "field": "value"},
                "operator": ">",
                "right": {"source": "indicator", "indicator": "SMA", "params": {"window": 200}, "field": "value"},
            },
            {
                "type": "news_feature",
                "feature": "sentiment_mean",
                "lookback_days": 7,
                "operator": ">",
                "value": 0.2,
            },
        ],
    },
    "exit": {
        "logic": "or",
        "conditions": [
            {
                "type": "indicator_compare",
                "left": {"source": "indicator", "indicator": "RSI", "params": {"window": 14}, "field": "value"},
                "operator": ">",
                "right": {"source": "constant", "value": 70},
            },
            {
                "type": "news_feature",
                "feature": "sentiment_mean",
                "lookback_days": 3,
                "operator": "<",
                "value": 0,
            },
        ],
    },
    "position_sizing": {"mode": "fixed_fraction", "fraction": 0.15, "max_positions": 8},
}

DSL_SAMPLES: List[Dict[str, object]] = [SMA_CROSSOVER_SPEC, RSI_MEAN_REVERSION_SPEC, TREND_NEWS_SPEC]


@pytest.fixture()
def strategy_registry(tmp_path) -> StrategyRegistry:
    repo = StrategyRepository(tmp_path / "strategies.db")
    return StrategyRegistry(repo)


def test_dsl_examples_validate_successfully():
    for sample in DSL_SAMPLES:
        valid, errors = validate_strategy_spec(sample)
        assert valid, f"Expected spec to be valid but found errors: {errors}"


def test_invalid_spec_reports_all_errors():
    invalid_spec = {
        "entry": {
            "logic": "xor",
            "conditions": [
                {
                    "type": "indicator_compare",
                    "left": {"source": "constant", "value": 1},
                    "operator": "??",
                    "right": {"source": "indicator", "indicator": 123},
                }
            ],
        }
    }
    valid, errors = validate_strategy_spec(invalid_spec)
    assert not valid
    assert any("logic" in err["path"] for err in errors)
    assert any("operator" in err["path"] for err in errors)
    assert any("indicator" in err["path"] for err in errors)


def test_strategy_registry_create_and_list(strategy_registry: StrategyRegistry):
    result = strategy_registry.create_strategy(
        user_id="user_1",
        name="SMA Trend",
        description="50/200 cross",
        json_spec=SMA_CROSSOVER_SPEC,
        nl_summary="Follows trend",
        origin="user",
        created_by="user_1",
    )
    strategy = result["strategy"]
    version = result["version"]
    assert strategy.current_version_id == version.id

    listed = strategy_registry.list_strategies(user_id="user_1")
    assert len(listed) == 1
    assert listed[0].id == strategy.id


def test_strategy_registry_versioning_flow(strategy_registry: StrategyRegistry):
    created = strategy_registry.create_strategy(
        user_id="user_1",
        name="RSI mean reversion",
        description="Buy oversold",
        json_spec=RSI_MEAN_REVERSION_SPEC,
        nl_summary="RSI bounce",
        origin="user",
        created_by="user_1",
    )
    strategy = created["strategy"]

    new_version = strategy_registry.create_version(
        strategy_id=strategy.id,
        json_spec=TREND_NEWS_SPEC,
        nl_summary="Trend plus news",
        origin="agent",
        created_by="agent_system",
    )

    refreshed = strategy_registry.get_strategy(strategy.id)
    assert refreshed.current_version_id == new_version.id

    all_versions = strategy_registry.list_versions(strategy_id=strategy.id)
    assert len(all_versions) == 2
    assert {version.id for version in all_versions} == {created["version"].id, new_version.id}


def test_strategy_registry_rejects_invalid_spec(strategy_registry: StrategyRegistry):
    with pytest.raises(StrategySpecError):
        strategy_registry.create_strategy(
            user_id="user_2",
            name="bad strategy",
            description=None,
            json_spec={"entry": {"logic": "and", "conditions": []}},
            nl_summary=None,
            origin="user",
            created_by="user_2",
        )
