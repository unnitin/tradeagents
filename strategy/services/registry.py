from __future__ import annotations

from typing import Any, Dict, Optional

from ..store import StrategyRepository
from .validation import validate_strategy_spec


class StrategySpecError(Exception):
    """Raised when a strategy DSL payload fails validation."""

    def __init__(self, errors: Any) -> None:
        super().__init__("Invalid strategy specification")
        self.errors = errors


class StrategyRegistry:
    """Facade for CRUD, versioning, and validation workflows."""

    def __init__(self, repository: StrategyRepository) -> None:
        self.repository = repository

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
        self._validate(json_spec)
        return self.repository.create_strategy(
            user_id=user_id,
            name=name,
            description=description,
            json_spec=json_spec,
            nl_summary=nl_summary,
            origin=origin,
            created_by=created_by,
        )

    def create_version(
        self,
        *,
        strategy_id: str,
        json_spec: Dict[str, Any],
        nl_summary: Optional[str],
        origin: Optional[str],
        created_by: Optional[str],
    ):
        self._validate(json_spec)
        return self.repository.create_version(
            strategy_id=strategy_id,
            json_spec=json_spec,
            nl_summary=nl_summary,
            origin=origin,
            created_by=created_by,
        )

    def list_strategies(self, *, user_id: str):
        return self.repository.list_strategies(user_id=user_id)

    def get_strategy(self, strategy_id: str):
        return self.repository.get_strategy(strategy_id)

    def list_versions(self, *, strategy_id: str):
        return self.repository.list_versions(strategy_id=strategy_id)

    def get_version(self, version_id: str):
        return self.repository.get_version(version_id)

    @staticmethod
    def validate_spec(spec: Dict[str, Any]):
        return validate_strategy_spec(spec)

    @staticmethod
    def _validate(spec: Dict[str, Any]) -> None:
        is_valid, errors = validate_strategy_spec(spec)
        if not is_valid:
            raise StrategySpecError(errors)
