# Backend service quickstart

## What lives here
- Flask app exposing health, price history (`/data/prices`), and feature computation (`/features`).
- Data providers: Yahoo Finance-backed market + news providers (default), pluggable via `DataGateway`.
- Feature engineering helpers for SMA/EMA/returns/volatility.
- Test utilities include a deterministic synthetic data provider used in unit tests.
- Automation utilities (`backend/utils/data_refresh.py`) for backfills/incremental updates of prices/features, plus news and trade disclosures into SQLite.
- Environment-aware automation config defined in `backend/config/data-settings.yaml` and loaded via `backend/utils/config_parser.py`.
- Cache read endpoints: `/cache/prices`, `/cache/features`, `/cache/news`, `/cache/trades` for data served from the SQLite store.
- Refresh endpoint: `POST /refresh` to trigger incremental updates using configured providers.
- Production entrypoint via Gunicorn: `gunicorn -b 0.0.0.0:8000 backend.wsgi:app`.
- Containerization: see `Dockerfile` for a minimal Python 3.11 image build.

## Running locally
1. Create and activate a virtualenv.
2. Install dependencies: `python3 -m pip install -r requirements.txt`.
3. Run the server: `FLASK_APP=backend.app flask run` (or `python -m backend.app` if you wrap an entrypoint).
4. Try it out: `curl "http://127.0.0.1:5000/data/prices?symbol=AAPL&start_date=2024-01-01&end_date=2024-01-05"`.
5. Production-style run: `gunicorn -b 0.0.0.0:8000 backend.wsgi:app`.

## Tests
- Run `python3 -m pytest` (uses the synthetic provider to avoid external calls).
- Automation: use `backend/utils/data_refresh.py` helpers (`run_backfill` / `run_incremental_update`, news/trades variants) or the wrapper `backend/automation.py:seed_from_config`. Configuration for dev/prod lives in `backend/config/data-settings.yaml` (parsed via `backend/utils/config_parser.py`).
- Lint: `python3 -m pip install -r requirements-dev.txt && ruff .`

## Git hooks / linting
We use [pre-commit](https://pre-commit.com/) to lint both the backend (ruff) and the frontend (ESLint) before every commit.

1. Install tooling once: `python3 -m pip install pre-commit` and `npm install --prefix frontend`.
2. Enable hooks: `pre-commit install`.
3. (Optional) Run against the repo: `pre-commit run --all-files`.

The hooks are defined in `.pre-commit-config.yaml` at the repo root. Ruff runs on all tracked Python files; the frontend hook shells into `frontend/` and executes `npm run lint`, so ensure that dependencies are installed before committing.

## Persistence / database notes
- Short term: in-memory app; no DB needed for stateless data proxy + feature calc.
- Next step: add a lightweight store (SQLite/Postgres) for request auditing, feature caching, and rate-limit metadata.
- Longer term: move to Postgres with read replicas; add Redis for caching aggregates and throttling.

## Next Steps
- Add connectors to news, politician and other data providers
- Backfill OHCLV data at 15m frequency for last 3 years of all US stocks (excl penny stocks)
- Backfill news and other trade trackers to min(the extent of data availability, 3 years)
- Add technical features such as bollinger bands, RS etc. 

## Path to production hardening
- Add retry/backoff + circuit breakers around Yahoo providers; surface dependency health in `/health`.
- Introduce request metrics/tracing (OpenTelemetry) and structured logging.
- Add input validation schemas (pydantic) and tighter error models.
- Scale via Gunicorn/Uvicorn + horizontal pods; cache hot symbols/features.
- Security: authn/z middleware, secrets management, and outbound call allowlisting.

## Backfill guidance (SQLite caches)
- Use `backend/utils/data_refresh.py` helpers: `run_backfill_prices` for a clean seed, `run_incremental_update_prices` for ongoing upserts; equivalent helpers exist for news/trades. For a simple local seed, run `python -m backend.automation` which reads `backend/config/data-settings.yaml` (dev env by default) and seeds using those ticker/time settings.
- Rough timing: backfilling the top ~200 symbols for ~4 weeks of daily bars is typically on the order of 1–2 minutes end-to-end if the provider responds in ~100–300 ms per symbol. Slower providers (1–2s/symbol) or rate limits can push this to ~5–7 minutes; feature computation and SQLite writes are negligible compared to network.
- Parameterize by environment: symbol universe, interval (e.g., `1d` vs `15m`), feature set, lookback window, and DB path should be configurable (e.g., `.env` or config file) so dev can stay lightweight while prod uses the full universe.
- Storage: local SQLite at `data.db` works for dev. A mounted volume like `/Volumes/fast-expansion` is present but currently not writable from this environment; confirm write permissions before using it for shared caches.
