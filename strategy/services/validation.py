from __future__ import annotations

from typing import Any, Dict, List, Tuple


ComparisonSet = {">", "<", ">=", "<=", "==", "!="}
LogicSet = {"and", "or"}
PositionSizingModes = {"fixed_fraction", "equal_weight"}
OrderTypes = {"market", "limit"}
TimeInForceValues = {"day", "gtc"}
RebalanceValues = {"daily_close", "weekly_close", "monthly"}


def validate_strategy_spec(spec: Dict[str, Any]) -> Tuple[bool, List[Dict[str, str]]]:
    errors: List[Dict[str, str]] = []

    if not isinstance(spec, dict):
        return False, [{"path": "", "message": "Strategy spec must be a JSON object."}]

    schema_version = spec.get("schema_version", "1.0")
    if not isinstance(schema_version, str):
        errors.append({"path": "schema_version", "message": "schema_version must be a string such as '1.0'."})
    timeframe = spec.get("timeframe", "1d")
    if not isinstance(timeframe, str):
        errors.append({"path": "timeframe", "message": "timeframe must be a string like '1d' or '1h'."})

    _validate_universe(spec.get("universe"), "universe", errors)
    _validate_logic_block(spec.get("entry"), "entry", errors, required=True)
    _validate_logic_block(spec.get("exit"), "exit", errors, required=False)
    _validate_position_sizing(spec.get("position_sizing"), "position_sizing", errors)
    _validate_risk(spec.get("risk"), "risk", errors)
    _validate_execution(spec.get("execution"), "execution", errors)

    return len(errors) == 0, errors


def _validate_universe(value: Any, path: str, errors: List[Dict[str, str]]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append({"path": path, "message": "universe must be an object with type/value."})
        return
    universe_type = value.get("type")
    universe_value = value.get("value")
    if universe_type not in {"preset", "filter", "tickers"}:
        errors.append({"path": f"{path}.type", "message": "type must be preset, filter, or tickers."})
    if universe_value is None:
        errors.append({"path": f"{path}.value", "message": "value is required for the universe definition."})


def _validate_logic_block(value: Any, path: str, errors: List[Dict[str, str]], *, required: bool) -> None:
    if value is None:
        if required:
            errors.append({"path": path, "message": "entry block is required."})
        return
    if not isinstance(value, dict):
        errors.append({"path": path, "message": f"{path} must be an object with logic and conditions."})
        return
    logic = value.get("logic")
    conditions = value.get("conditions")
    if logic not in LogicSet:
        errors.append({"path": f"{path}.logic", "message": f"logic must be one of {sorted(LogicSet)}."})
    if conditions is None:
        errors.append({"path": f"{path}.conditions", "message": "conditions list is required."})
        return
    if not isinstance(conditions, list):
        errors.append({"path": f"{path}.conditions", "message": "conditions must be a list."})
        return
    if len(conditions) == 0 and required:
        errors.append({"path": f"{path}.conditions", "message": "Provide at least one condition."})
    for idx, condition in enumerate(conditions):
        _validate_condition(condition, f"{path}.conditions[{idx}]", errors)


def _validate_condition(condition: Any, path: str, errors: List[Dict[str, str]]) -> None:
    if not isinstance(condition, dict):
        errors.append({"path": path, "message": "Condition must be an object."})
        return
    condition_type = condition.get("type")
    if condition_type not in {"indicator_compare", "indicator_cross", "news_feature", "composite"}:
        errors.append(
            {
                "path": f"{path}.type",
                "message": "Unknown condition type. Use indicator_compare, indicator_cross, news_feature, or composite.",
            }
        )
        return
    if condition_type == "indicator_compare":
        _validate_indicator_compare(condition, path, errors)
    elif condition_type == "indicator_cross":
        _validate_indicator_cross(condition, path, errors)
    elif condition_type == "news_feature":
        _validate_news_feature(condition, path, errors)
    elif condition_type == "composite":
        _validate_composite(condition, path, errors)


def _validate_indicator_compare(condition: Dict[str, Any], path: str, errors: List[Dict[str, str]]) -> None:
    operator = condition.get("operator")
    if operator not in ComparisonSet:
        errors.append({"path": f"{path}.operator", "message": f"operator must be one of {sorted(ComparisonSet)}."})
    _validate_operand(condition.get("left"), f"{path}.left", errors, allow_constant=False)
    _validate_operand(condition.get("right"), f"{path}.right", errors, allow_constant=True)


def _validate_indicator_cross(condition: Dict[str, Any], path: str, errors: List[Dict[str, str]]) -> None:
    direction = condition.get("direction")
    if direction not in {"up", "down"}:
        errors.append({"path": f"{path}.direction", "message": "direction must be 'up' or 'down'."})
    for side in ("fast", "slow"):
        _validate_indicator(condition.get(side), f"{path}.{side}", errors)


def _validate_news_feature(condition: Dict[str, Any], path: str, errors: List[Dict[str, str]]) -> None:
    feature = condition.get("feature")
    if not isinstance(feature, str):
        errors.append({"path": f"{path}.feature", "message": "feature must be a string (e.g., sentiment_mean)."})
    lookback = condition.get("lookback_days")
    if not isinstance(lookback, int) or lookback <= 0:
        errors.append({"path": f"{path}.lookback_days", "message": "lookback_days must be a positive integer."})
    operator = condition.get("operator")
    if operator not in ComparisonSet:
        errors.append({"path": f"{path}.operator", "message": f"operator must be one of {sorted(ComparisonSet)}."})
    value = condition.get("value")
    if not isinstance(value, (int, float)):
        errors.append({"path": f"{path}.value", "message": "value must be numeric."})


def _validate_composite(condition: Dict[str, Any], path: str, errors: List[Dict[str, str]]) -> None:
    logic = condition.get("logic")
    if logic not in LogicSet:
        errors.append({"path": f"{path}.logic", "message": f"logic must be one of {sorted(LogicSet)}."})
    sub_conditions = condition.get("conditions")
    if not isinstance(sub_conditions, list) or not sub_conditions:
        errors.append({"path": f"{path}.conditions", "message": "composite conditions must be a non-empty list."})
        return
    for idx, child in enumerate(sub_conditions):
        _validate_condition(child, f"{path}.conditions[{idx}]", errors)


def _validate_operand(value: Any, path: str, errors: List[Dict[str, str]], *, allow_constant: bool) -> None:
    if not isinstance(value, dict):
        errors.append({"path": path, "message": "Operand must be an object."})
        return
    source = value.get("source")
    if source == "indicator":
        _validate_indicator(value, path, errors)
    elif source == "constant":
        if not allow_constant:
            errors.append({"path": path, "message": "This operand must reference an indicator source."})
            return
        if "value" not in value:
            errors.append({"path": f"{path}.value", "message": "constant operands require a numeric value."})
        elif not isinstance(value["value"], (int, float)):
            errors.append({"path": f"{path}.value", "message": "constant value must be numeric."})
    else:
        errors.append({"path": f"{path}.source", "message": "source must be 'indicator' or 'constant'."})


def _validate_indicator(value: Any, path: str, errors: List[Dict[str, str]]) -> None:
    if not isinstance(value, dict):
        errors.append({"path": path, "message": "Indicator definition must be an object."})
        return
    if not isinstance(value.get("indicator"), str):
        errors.append({"path": f"{path}.indicator", "message": "indicator must be a string (e.g., SMA, RSI)."})
    params = value.get("params", {})
    if params is not None and not isinstance(params, dict):
        errors.append({"path": f"{path}.params", "message": "params must be an object."})
    field = value.get("field")
    if field is not None and not isinstance(field, str):
        errors.append({"path": f"{path}.field", "message": "field must be a string when provided."})


def _validate_position_sizing(value: Any, path: str, errors: List[Dict[str, str]]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append({"path": path, "message": "position_sizing must be an object."})
        return
    mode = value.get("mode")
    if mode not in PositionSizingModes:
        errors.append(
            {
                "path": f"{path}.mode",
                "message": f"mode must be one of {sorted(PositionSizingModes)} (see DSL examples).",
            }
        )
        return
    if mode == "fixed_fraction":
        fraction = value.get("fraction")
        if not isinstance(fraction, (int, float)) or not 0 < fraction <= 1:
            errors.append({"path": f"{path}.fraction", "message": "fraction must be between 0 and 1."})
    max_positions = value.get("max_positions")
    if not isinstance(max_positions, int) or max_positions <= 0:
        errors.append({"path": f"{path}.max_positions", "message": "max_positions must be a positive integer."})


def _validate_risk(value: Any, path: str, errors: List[Dict[str, str]]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append({"path": path, "message": "risk must be an object."})
        return
    max_gross = value.get("max_gross_exposure")
    if max_gross is not None and (not isinstance(max_gross, (int, float)) or max_gross <= 0):
        errors.append({"path": f"{path}.max_gross_exposure", "message": "Must be a positive number."})
    single_pct = value.get("max_single_position_pct")
    if single_pct is not None and (not isinstance(single_pct, (int, float)) or not 0 < single_pct <= 1.5):
        errors.append({"path": f"{path}.max_single_position_pct", "message": "Provide a sensible fraction (0-1.5)."})
    for key in ("stop_loss", "take_profit"):
        if key in value:
            _validate_risk_trigger(value[key], f"{path}.{key}", errors)


def _validate_risk_trigger(value: Any, path: str, errors: List[Dict[str, str]]) -> None:
    if not isinstance(value, dict):
        errors.append({"path": path, "message": "Risk trigger must be an object with type/value."})
        return
    if value.get("type") not in {"pct", "trailing_pct"}:
        errors.append({"path": f"{path}.type", "message": "type must be pct or trailing_pct."})
    trigger_value = value.get("value")
    if not isinstance(trigger_value, (int, float)) or trigger_value <= 0:
        errors.append({"path": f"{path}.value", "message": "value must be a positive number."})


def _validate_execution(value: Any, path: str, errors: List[Dict[str, str]]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append({"path": path, "message": "execution must be an object."})
        return
    order_type = value.get("order_type")
    if order_type is not None and order_type not in OrderTypes:
        errors.append({"path": f"{path}.order_type", "message": f"order_type must be one of {sorted(OrderTypes)}."})
    tif = value.get("time_in_force")
    if tif is not None and tif not in TimeInForceValues:
        errors.append(
            {"path": f"{path}.time_in_force", "message": f"time_in_force must be one of {sorted(TimeInForceValues)}."}
        )
    rebalance = value.get("rebalance")
    if rebalance is not None and rebalance not in RebalanceValues:
        errors.append(
            {"path": f"{path}.rebalance", "message": f"rebalance must be one of {sorted(RebalanceValues)}."}
        )
