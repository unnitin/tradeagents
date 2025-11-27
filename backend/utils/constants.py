"""Shared constants for backend service."""
from __future__ import annotations

from pathlib import Path

import yaml

from .config_parser import load_automation_config

DATE_FORMAT = "%Y-%m-%d"

_DEFAULT_AUTOMATION_ENV = "dev"
_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "data-settings.yaml"

# TODO: DATA_DB_PATH to be set as a required argument for the file that runs the features, remove the helper functions from this file
def _get_configured_env() -> str:
    """Determine which automation environment should be used by defaults.

    Returns:
        Environment key to load from the automation config.

    Raises:
        RuntimeError: If the config file lacks environments or references a missing one.
    """
    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}

    environments = config.get("environments") or {}
    if not environments:
        raise RuntimeError("No environments defined in automation config")

    target_env = config.get("env") or config.get("default_env")
    if target_env:
        if target_env not in environments:
            raise RuntimeError(f"Configured env '{target_env}' missing from automation config")
        return target_env

    if _DEFAULT_AUTOMATION_ENV in environments:
        return _DEFAULT_AUTOMATION_ENV

    return next(iter(environments))


def _resolve_db_path() -> str:
    """Resolve the configured path to the data database for the active environment.

    Returns:
        Path to the database file defined in the environment storage section.

    Raises:
        RuntimeError: If the storage section does not include an explicit path.
    """
    env = _get_configured_env()
    storage_cfg = load_automation_config(env).storage
    if storage_cfg.path:
        return storage_cfg.path
    raise RuntimeError(f"Storage path missing in automation config for env '{env}'")


DATA_DB_PATH = _resolve_db_path()

# Default feature set computed for price backfills/updates.
PRICE_DEFAULT_FEATURES = ["return_pct", "sma_5", "ema_10", "volatility_5"]

# Default lookbacks for cached data domains.
NEWS_DEFAULT_LOOKBACK_DAYS = 30
TRADES_DEFAULT_LOOKBACK_DAYS = 30
