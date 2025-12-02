from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


@dataclass
class StrategyRecord:
    id: str
    user_id: str
    name: str
    description: Optional[str]
    current_version_id: Optional[str]
    origin_latest: Optional[str]
    created_at: str
    updated_at: str


@dataclass
class StrategyVersionRecord:
    id: str
    strategy_id: str
    json_spec: Dict[str, Any]
    nl_summary: Optional[str]
    origin: Optional[str]
    created_by: Optional[str]
    created_at: str


class StrategyRepository:
    """SQLite-backed persistence for strategy metadata and versions."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS strategies (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    current_version_id TEXT,
                    origin_latest TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS strategy_versions (
                    id TEXT PRIMARY KEY,
                    strategy_id TEXT NOT NULL,
                    json_spec TEXT NOT NULL,
                    nl_summary TEXT,
                    origin TEXT,
                    created_by TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_versions_strategy ON strategy_versions(strategy_id)")
            conn.commit()

    # CRUD helpers ---------------------------------------------------------

    def create_strategy(
        self,
        *,
        user_id: str,
        name: str,
        description: Optional[str],
        json_spec: Dict[str, Any],
        nl_summary: Optional[str],
        origin: Optional[str],
        created_by: Optional[str],
    ) -> Dict[str, Any]:
        strategy_id = f"s_{uuid.uuid4().hex}"
        version_id = f"sv_{uuid.uuid4().hex}"
        now = _utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO strategies (id, user_id, name, description, current_version_id, origin_latest, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (strategy_id, user_id, name, description, version_id, origin, now, now),
            )
            conn.execute(
                """
                INSERT INTO strategy_versions (id, strategy_id, json_spec, nl_summary, origin, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    strategy_id,
                    json.dumps(json_spec),
                    nl_summary,
                    origin,
                    created_by,
                    now,
                ),
            )
            conn.commit()

        strategy = self.get_strategy(strategy_id)
        version = self.get_version(version_id)
        return {"strategy": strategy, "version": version}

    def list_strategies(self, *, user_id: str) -> List[StrategyRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, name, description, current_version_id, origin_latest, created_at, updated_at
                FROM strategies
                WHERE user_id = ?
                ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [StrategyRecord(**_row_to_dict(row)) for row in rows]

    def get_strategy(self, strategy_id: str) -> StrategyRecord:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, name, description, current_version_id, origin_latest, created_at, updated_at
                FROM strategies
                WHERE id = ?
                """,
                (strategy_id,),
            ).fetchone()
        if not row:
            raise KeyError(f"Strategy {strategy_id} not found")
        return StrategyRecord(**_row_to_dict(row))

    def create_version(
        self,
        *,
        strategy_id: str,
        json_spec: Dict[str, Any],
        nl_summary: Optional[str],
        origin: Optional[str],
        created_by: Optional[str],
    ) -> StrategyVersionRecord:
        _ = self.get_strategy(strategy_id)  # ensure exists
        version_id = f"sv_{uuid.uuid4().hex}"
        now = _utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO strategy_versions (id, strategy_id, json_spec, nl_summary, origin, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    strategy_id,
                    json.dumps(json_spec),
                    nl_summary,
                    origin,
                    created_by,
                    now,
                ),
            )
            conn.execute(
                """
                UPDATE strategies
                SET current_version_id = ?, origin_latest = ?, updated_at = ?
                WHERE id = ?
                """,
                (version_id, origin, now, strategy_id),
            )
            conn.commit()
        return self.get_version(version_id)

    def list_versions(self, *, strategy_id: str) -> List[StrategyVersionRecord]:
        _ = self.get_strategy(strategy_id)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, strategy_id, json_spec, nl_summary, origin, created_by, created_at
                FROM strategy_versions
                WHERE strategy_id = ?
                ORDER BY created_at DESC
                """,
                (strategy_id,),
            ).fetchall()
        return [self._row_to_version(row) for row in rows]

    def get_version(self, version_id: str) -> StrategyVersionRecord:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, strategy_id, json_spec, nl_summary, origin, created_by, created_at
                FROM strategy_versions
                WHERE id = ?
                """,
                (version_id,),
            ).fetchone()
        if not row:
            raise KeyError(f"Strategy version {version_id} not found")
        return self._row_to_version(row)

    def _row_to_version(self, row: sqlite3.Row) -> StrategyVersionRecord:
        data = _row_to_dict(row)
        data["json_spec"] = json.loads(data["json_spec"])
        return StrategyVersionRecord(**data)
