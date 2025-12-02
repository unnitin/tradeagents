# Trade platform monorepo

This repo hosts the core services, UI, and docs that power the conversational strategy-building experience. It is
organized as a light monorepo with dedicated submodules for each surface so teams can iterate independently but ship a
cohesive product.

## Repo structure
- `backend/` – Flask service for market data, feature engineering, caching, and automation tasks.
- `frontend/` – Vite + React client that showcases the end-to-end workflow (strategy creation, dashboards, agent chat).
- `strategy/` – New Strategy Service module dedicated to storing DSL specs, NL summaries, validation, and agent hooks.
- `docs/` – Specifications for APIs, flows, DSL examples, Docker/dev instructions, and product narratives.
- `tests/` – Shared integration/unit tests that stitch across modules where possible.

Each submodule owns its own README with deeper detail:
- [`backend/Readme.md`](backend/Readme.md)
- [`frontend/README.md`](frontend/README.md)
- [`strategy/README.md`](strategy/README.md)

## Getting started
1. Clone the repo and install Python 3.11 + Node 20.x (or the versions pinned in `pyproject.toml`/`package.json`).
2. (Optional) Install `pre-commit` and run `pre-commit install` to keep linters in sync across modules.
3. Spin up services as needed:
   - Backend: follow `backend/README.md` for virtualenv setup, Flask dev server, and automation helpers.
   - Frontend: follow `frontend/README.md` for Vite dev server or Docker compose instructions.
   - Strategy: FastAPI microservice that exposes strategy registry/versioning/validation. Run `uvicorn strategy.app:app --reload --port 8100`
     or `docker compose -f docker-compose.strategy.yml up` for containerized dev.
4. Use the compose files (`docker-compose.backend.yml`, `docker-compose.frontend.yml`, `docker-compose.strategy.yml`) to
   run individual services locally when integrating the UI with live APIs.

## Guiding principles
- **NL-first workflows** – everything originates from natural language chats; JSON DSL and code are derived artifacts.
- **Versioned truth** – strategies, backtests, and agent messages keep full history so revisions are auditable.
- **Modularity** – each module exposes clear contracts (REST + events) so teams can ship independently.
- **Automation friendly** – automation scripts + Docker flows exist for quick seeds, refreshes, and demos.

## Next steps for contributors
1. Fill out the Strategy Service implementation (FastAPI suggested) following `docs/api_spec.md`.
2. Expand frontend wiring to consume new strategy/backtest endpoints once available.
3. Harden backend automation (retry/backoff, scheduling) and unify logging/auth across services.
4. Keep docs synchronized with reality—update `docs/api_spec.md` + submodule READMEs as endpoints evolve.
