# Strategy Service module

A Python-first service dedicated to storing, validating, and iterating on trading strategy definitions. It mirrors the
main `backend/` Flask app in structure (package entrypoint, config surface, future tests) but focuses solely on
strategy lifecycle workflows described in `docs/api_spec.md` and `docs/system-design.md`.

## Objectives
- Persist every strategy as a versioned JSON spec paired with natural-language summaries and origin metadata (backed by SQLite for now).
- Offer APIs for creation, validation, listing, retrieval, and refinement hooks used by UI + agent flows.
- Act as the single source of truth for `strategy_version_id` that downstream systems (backtests, chat, dashboards) rely on.
- Provide governance + audit features (who created a version, what changed, when) so conversations can cite history.

## Current layout
```
strategy/
├── README.md               # This document
├── app.py                  # FastAPI application + routers
├── config.py               # Environment-driven settings (db path, etc.)
├── services/
│   ├── registry.py         # High-level CRUD/versioning facade + validation hooks
│   └── validation.py       # DSL validator informed by docs/strategy_dsl_examples.md
├── store/
│   └── sqlite_repository.py# SQLite repository for strategies/version history
├── tests/
│   └── test_validation.py  # Ensures exemplar DSL payloads stay valid
└── Dockerfile              # Container image definition (served via uvicorn)
```

## Key responsibilities
1. **Strategy CRUD** – `/strategies`, `/strategies/{id}`, `/strategies/{id}/versions`, `/strategy-versions/{version_id}` all backed by SQLite persistence. Each write updates `current_version_id` plus `origin_latest`.
2. **Strategy registry** – `GET /strategies?user_id=...` lists a user’s strategies so UI + chat can select them.
3. **Version history** – `GET /strategies/{id}/versions` exposes provenance while version-specific reads fetch the full DSL payload.
4. **DSL validation engine** – `/strategies/validate` executes the same validator used on writes. The validator references the scenarios laid out in `docs/strategy_dsl_examples.md` (SMA crossover, news filters, composites, etc.) so common patterns stay first-class.
5. **Deployment parity** – dedicated Dockerfile + compose entry (`docker-compose.strategy.yml`) so the service can run alongside backend/frontend containers.

## Run locally
```bash
pip install -r requirements.txt
uvicorn strategy.app:app --reload --port 8100
# SQLite database path can be overridden via STRATEGY_DB_PATH=/path/to/db
```

## Docker
```bash
docker compose -f docker-compose.strategy.yml up --build
```
The container exposes port `8100` with a bind-mounted `data/` directory to persist the SQLite file between runs.

## Implementation notes
- FastAPI + Pydantic power the REST surface while `sqlite3` keeps persistence lightweight. Swap the repo implementation for SQLAlchemy/Postgres when multi-instance scaling is required.
- `strategy/services/validation.py` enforces the DSL structure (logic blocks, indicator/news condition schemas, risk/position sizing contract). Reference tests mirror payloads in `docs/strategy_dsl_examples.md` to ensure typical trend/mean-reversion/news cases validate successfully.
- IDs are minted with UUID prefixes (`s_`, `sv_`) so they align with the API spec and remain opaque to clients.
- The registry facade (`StrategyRegistry`) centralizes validation so programmatic callers and API handlers stay in sync.

## Roadmap ideas
1. **Diff + compare endpoint** – highlight JSON & NL changes between versions to improve chat explanations.
2. **Strategy templates** – store curated DSL templates (trend, mean reversion, event-driven) that agents/users can clone.
3. **Agent helpers** – internal endpoints for `/agent/strategies/from-text` and `/agent/strategies/{version_id}/refine` once the orchestration service is ready.
4. **Performance snapshots** – cache latest backtest metrics per strategy to accelerate dashboards once integrated with the Backtest service.
5. **Access control** – workspace/user scoping with JWT or API key auth to ensure strategies stay in the right org.
