"""Config loader utilities for automation and other backend services."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Sequence

import yaml


@dataclass(frozen=True)
class PriceConfig:
    tickers: Sequence[str]
    lookback_days: int
    interval: str = "1d"


@dataclass(frozen=True)
class StorageConfig:
    engine: str
    location: str
    path: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class DomainConfig:
    provider: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class EnvironmentConfig:
    env: str
    location: str
    storage: StorageConfig
    price: PriceConfig
    news: DomainConfig = field(default_factory=DomainConfig)
    trades: DomainConfig = field(default_factory=DomainConfig)


def load_automation_config(env: str, config_path: Path | None = None) -> EnvironmentConfig:
    path = config_path or Path(__file__).resolve().parents[1] / "config" / "data-settings.yaml"
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    envs: Mapping[str, dict] = raw.get("environments", {})
    if env not in envs:
        raise ValueError(f"Unknown automation env '{env}'. Available: {', '.join(envs)}")
    cfg = envs[env]
    return EnvironmentConfig(
        env=cfg["env"],
        location=cfg["location"],
        storage=StorageConfig(**cfg["storage"]),
        price=PriceConfig(**cfg["price"]),
        news=DomainConfig(**cfg.get("news", {})),
        trades=DomainConfig(**cfg.get("trades", {})),
    )
