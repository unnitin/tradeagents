"""Feature engineering helpers for the backend service."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Union

from .data_provider import PriceCandle


class FeatureEngineeringError(ValueError):
    """Raised when a feature request is invalid."""


FeatureRow = Dict[str, Union[str, Optional[float]]]


def compute_features(candles: List[PriceCandle], requested_features: Iterable[str]) -> List[FeatureRow]:
    """Compute the requested features for every candle in the series.

    Args:
        candles: Ordered OHLCV records used as raw inputs.
        requested_features: Iterable of feature identifiers (e.g., sma_5).

    Returns:
        List of dicts where each dict is keyed by feature name and includes the candle date.

    Raises:
        FeatureEngineeringError: If the feature list is empty or contains unsupported names.
    """

    feature_list = list(requested_features)
    if not feature_list:
        raise FeatureEngineeringError("features list cannot be empty")

    close_prices = [candle.close for candle in candles]
    returns = _compute_returns(close_prices)

    computed: Dict[str, List[Optional[float]]] = {}
    for name in feature_list:
        if name == "return_pct":
            computed[name] = returns
        elif name.startswith("sma_"):
            window = _parse_window(name, prefix="sma_")
            computed[name] = _simple_moving_average(close_prices, window)
        elif name.startswith("ema_"):
            window = _parse_window(name, prefix="ema_")
            computed[name] = _exponential_moving_average(close_prices, window)
        elif name.startswith("volatility_"):
            window = _parse_window(name, prefix="volatility_")
            computed[name] = _rolling_volatility(returns, window)
        else:
            raise FeatureEngineeringError(f"unsupported feature '{name}'")

    feature_rows: List[FeatureRow] = []
    for idx, candle in enumerate(candles):
        row: FeatureRow = {"date": candle.date.isoformat()}
        for feature_name in feature_list:
            value = computed[feature_name][idx]
            if value is None:
                row[feature_name] = None
            else:
                row[feature_name] = round(value, 4)
        feature_rows.append(row)

    return feature_rows


def _parse_window(feature_name: str, prefix: str) -> int:
    """Extract the trailing integer window length from a feature name.

    Args:
        feature_name: Original string such as "sma_10".
        prefix: Prefix to strip before parsing the integer portion.

    Returns:
        Positive integer window length used by moving calculations.

    Raises:
        FeatureEngineeringError: If the suffix cannot be parsed or is <= 1.
    """
    try:
        window = int(feature_name[len(prefix) :])
    except ValueError as exc:  # pragma: no cover - defensive
        raise FeatureEngineeringError(f"invalid window in feature '{feature_name}'") from exc

    if window <= 1:
        raise FeatureEngineeringError("window size must be greater than 1")

    return window


def _simple_moving_average(values: List[float], window: int) -> List[Optional[float]]:
    """Compute an SMA over the provided values.

    Args:
        values: Ordered numeric series.
        window: Number of data points that make up each average.

    Returns:
        List matching `values` length with None for insufficient history.
    """
    results: List[Optional[float]] = []
    cumulative = 0.0
    window_values: List[float] = []
    for value in values:
        window_values.append(value)
        cumulative += value
        if len(window_values) < window:
            results.append(None)
            continue
        if len(window_values) > window:
            cumulative -= window_values.pop(0)
        results.append(cumulative / window)
    return results


def _exponential_moving_average(values: List[float], window: int) -> List[Optional[float]]:
    """Compute an EMA over the provided values.

    Args:
        values: Ordered numeric series.
        window: Period length that determines the EMA multiplier.

    Returns:
        List matching `values` length with progressively populated EMA values.
    """
    results: List[Optional[float]] = []
    multiplier = 2 / (window + 1)
    ema: Optional[float] = None
    for value in values:
        if ema is None:
            ema = value
        else:
            ema = (value - ema) * multiplier + ema
        results.append(ema)
    return results


def _compute_returns(values: List[float]) -> List[Optional[float]]:
    """Compute simple percentage returns between consecutive values.

    Args:
        values: Close prices or other sequential numeric series.

    Returns:
        Percentage change per step with 0.0 for the first observation.
    """
    returns: List[Optional[float]] = []
    previous = None
    for value in values:
        if previous is None:
            returns.append(0.0)
        else:
            returns.append((value - previous) / previous)
        previous = value
    return returns


def _rolling_volatility(returns: List[Optional[float]], window: int) -> List[Optional[float]]:
    """Compute a rolling standard deviation over the provided returns.

    Args:
        returns: Percentage returns potentially containing None.
        window: Number of points in each rolling window.

    Returns:
        List containing volatility estimates (standard deviation) or None until enough history.
    """
    numeric_returns = [r if r is not None else 0.0 for r in returns]
    results: List[Optional[float]] = []
    window_values: List[float] = []
    for value in numeric_returns:
        window_values.append(value)
        if len(window_values) < window:
            results.append(None)
            continue
        if len(window_values) > window:
            window_values.pop(0)
        mean = sum(window_values) / window
        variance = sum((val - mean) ** 2 for val in window_values) / window
        results.append(variance ** 0.5)
    return results
