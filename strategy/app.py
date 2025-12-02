from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from .config import settings
from .services import StrategyRegistry, StrategySpecError
from .store import StrategyRepository


class StrategySummary(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    current_version_id: Optional[str] = None
    origin_latest: Optional[str] = None
    created_at: str
    updated_at: str


class StrategyVersionModel(BaseModel):
    id: str
    strategy_id: str
    json_spec: Dict[str, Any]
    nl_summary: Optional[str] = None
    origin: Optional[str] = None
    created_by: Optional[str] = None
    created_at: str


class StrategyCreateRequest(BaseModel):
    user_id: str
    name: str
    description: Optional[str] = None
    json_spec: Dict[str, Any]
    nl_summary: Optional[str] = None
    origin: Optional[Literal["user", "agent", "mixed"]] = "user"
    created_by: Optional[str] = None


class StrategyCreateResponse(BaseModel):
    strategy: StrategySummary
    version: StrategyVersionModel


class StrategyListResponse(BaseModel):
    items: List[StrategySummary]


class StrategyDetailResponse(BaseModel):
    strategy: StrategySummary
    current_version: Optional[StrategyVersionModel] = None


class VersionListResponse(BaseModel):
    items: List[StrategyVersionModel]


class StrategyVersionCreateRequest(BaseModel):
    json_spec: Dict[str, Any]
    nl_summary: Optional[str] = None
    origin: Optional[Literal["user", "agent", "mixed"]] = "mixed"
    created_by: Optional[str] = None


class StrategyValidateRequest(BaseModel):
    json_spec: Dict[str, Any] = Field(..., description="Strategy DSL payload to validate.")


class StrategyValidateResponse(BaseModel):
    valid: bool
    errors: List[Dict[str, str]]


def create_app() -> FastAPI:
    """Construct the FastAPI application for the Strategy service."""

    repository = StrategyRepository(settings.database_path)
    registry = StrategyRegistry(repository)

    app = FastAPI(title="Strategy Service", version="0.1.0")

    def get_registry() -> StrategyRegistry:
        return registry

    @app.get("/health", tags=["system"])
    def healthcheck() -> Dict[str, str]:
        return {"status": "ok"}

    @app.post("/strategies", response_model=StrategyCreateResponse, status_code=status.HTTP_201_CREATED, tags=["strategies"])
    def create_strategy(
        payload: StrategyCreateRequest, registry: StrategyRegistry = Depends(get_registry)
    ) -> StrategyCreateResponse:
        try:
            result = registry.create_strategy(**payload.model_dump())
        except StrategySpecError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"errors": exc.errors}) from exc
        strategy = _to_strategy_summary(result["strategy"])
        version = _to_version_model(result["version"])
        return StrategyCreateResponse(strategy=strategy, version=version)

    @app.get("/strategies", response_model=StrategyListResponse, tags=["strategies"])
    def list_strategies(
        user_id: str = Query(..., description="Filter strategies by owner"),
        registry: StrategyRegistry = Depends(get_registry),
    ) -> StrategyListResponse:
        items = [_to_strategy_summary(s) for s in registry.list_strategies(user_id=user_id)]
        return StrategyListResponse(items=items)

    @app.get("/strategies/{strategy_id}", response_model=StrategyDetailResponse, tags=["strategies"])
    def get_strategy(strategy_id: str, registry: StrategyRegistry = Depends(get_registry)) -> StrategyDetailResponse:
        try:
            strategy = registry.get_strategy(strategy_id)
        except KeyError as exc:
            _raise_not_found(exc)
        current_version = None
        if strategy.current_version_id:
            try:
                current_version = registry.get_version(strategy.current_version_id)
            except KeyError as exc:  # pragma: no cover - inconsistent db states
                _raise_not_found(exc)
        return StrategyDetailResponse(
            strategy=_to_strategy_summary(strategy),
            current_version=_to_version_model(current_version) if current_version else None,
        )

    @app.post(
        "/strategies/{strategy_id}/versions",
        response_model=StrategyVersionModel,
        status_code=status.HTTP_201_CREATED,
        tags=["versions"],
    )
    def create_strategy_version(
        strategy_id: str,
        payload: StrategyVersionCreateRequest,
        registry: StrategyRegistry = Depends(get_registry),
    ) -> StrategyVersionModel:
        try:
            version = registry.create_version(strategy_id=strategy_id, **payload.model_dump())
        except KeyError as exc:
            _raise_not_found(exc)
        except StrategySpecError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"errors": exc.errors}) from exc
        return _to_version_model(version)

    @app.get("/strategies/{strategy_id}/versions", response_model=VersionListResponse, tags=["versions"])
    def list_versions(strategy_id: str, registry: StrategyRegistry = Depends(get_registry)) -> VersionListResponse:
        try:
            items = registry.list_versions(strategy_id=strategy_id)
        except KeyError as exc:
            _raise_not_found(exc)
        return VersionListResponse(items=[_to_version_model(item) for item in items])

    @app.get("/strategy-versions/{version_id}", response_model=StrategyVersionModel, tags=["versions"])
    def get_version(version_id: str, registry: StrategyRegistry = Depends(get_registry)) -> StrategyVersionModel:
        try:
            version = registry.get_version(version_id)
        except KeyError as exc:
            _raise_not_found(exc)
        return _to_version_model(version)

    @app.post("/strategies/validate", response_model=StrategyValidateResponse, tags=["validation"])
    def validate_strategy(payload: StrategyValidateRequest) -> StrategyValidateResponse:
        valid, errors = StrategyRegistry.validate_spec(payload.json_spec)
        return StrategyValidateResponse(valid=valid, errors=errors)

    return app


def _to_strategy_summary(record: Any) -> StrategySummary:
    data = asdict(record)
    return StrategySummary(**data)


def _to_version_model(record: Any) -> StrategyVersionModel:
    data = asdict(record)
    return StrategyVersionModel(**data)


def _raise_not_found(exc: KeyError) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
