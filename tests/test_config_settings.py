"""Tests for validating backend configuration files such as data-settings.yaml."""
from __future__ import annotations

from pathlib import Path

import yaml

DATA_SETTINGS_PATH = Path("backend/config/data-settings.yaml")


def test_data_settings_yaml_is_valid_and_has_required_sections() -> None:
    """Ensure the data-settings YAML parses and contains the expected structure."""
    with DATA_SETTINGS_PATH.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    assert isinstance(config, dict), "Config root must be a mapping"
    environments = config.get("environments")
    assert isinstance(environments, dict) and environments, "Config must define environments"

    for env_name, env_cfg in environments.items():
        assert isinstance(env_cfg, dict), f"{env_name} config must be a mapping"
        for section in ("env", "location", "storage", "price"):
            assert section in env_cfg, f"{env_name} missing required '{section}' section"
        assert isinstance(env_cfg["storage"], dict), f"{env_name} storage section must be a mapping"
        assert isinstance(env_cfg["price"], dict), f"{env_name} price section must be a mapping"
        news_cfg = env_cfg.get("news")
        assert isinstance(news_cfg, dict), f"{env_name} news section must be a mapping"
        provider = news_cfg.get("provider")
        assert isinstance(provider, str) and provider, f"{env_name} news provider must be specified"
