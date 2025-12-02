from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    """Runtime configuration for the Strategy service."""

    database_path: Path

    @staticmethod
    def load() -> "Settings":
        base_data_dir = Path(os.environ.get("STRATEGY_DATA_DIR", "data")).expanduser()
        base_data_dir.mkdir(parents=True, exist_ok=True)
        db_path = Path(os.environ.get("STRATEGY_DB_PATH", base_data_dir / "strategies.db")).expanduser()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return Settings(database_path=db_path)


settings = Settings.load()
