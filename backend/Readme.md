# Backend service quickstart

## What lives here
- Flask app exposing health, price history (`/data/prices`), and feature computation (`/features`).
- Data providers: Yahoo Finance-backed market + news providers (default), pluggable via `DataGateway`.
- Feature engineering helpers for SMA/EMA/returns/volatility.
- Test utilities include a deterministic synthetic data provider used in unit tests.
- Automation utilities (`backend/automation.py`) for backfills/incremental updates of prices/features, plus news and trade disclosures into SQLite.
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
- Automation: use `run_backfill` / `run_incremental_update` (pass `YahooMarketDataProvider()`), `run_backfill_news` / `run_incremental_update_news` (requires `NewsDataProvider`), and equivalent trade helpers with a `TradeDataProvider`.
- Lint: `python3 -m pip install -r requirements-dev.txt && ruff .`

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
- Use `automation.py` helpers: `run_backfill_prices` for a clean seed, `run_incremental_update_prices` for ongoing upserts; equivalent helpers exist for news/trades.
- Rough timing: backfilling the top ~200 symbols for ~4 weeks of daily bars is typically on the order of 1–2 minutes end-to-end if the provider responds in ~100–300 ms per symbol. Slower providers (1–2s/symbol) or rate limits can push this to ~5–7 minutes; feature computation and SQLite writes are negligible compared to network.
- Parameterize by environment: symbol universe, interval (e.g., `1d` vs `15m`), feature set, lookback window, and DB path should be configurable (e.g., `.env` or config file) so dev can stay lightweight while prod uses the full universe.
- Storage: local SQLite at `data.db` works for dev. A mounted volume like `/Volumes/fast-expansion` is present but currently not writable from this environment; confirm write permissions before using it for shared caches.
