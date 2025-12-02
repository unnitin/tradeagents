# TradeAgent Studio frontend

A Vite + React + TypeScript prototype that mirrors the warm serif/sans palette defined in `front-end-mockup/`.
It illustrates how clients collaborate with AI agents to create, backtest, and discuss trading strategies while
surfacing market data, features, news, and backtest summaries.

## Current functionality (UI)
- **Home page** – hero + navigation, call-to-actions for strategy creation/review, and messaging about AI + human collaboration.
- **Strategy workspace** – pipeline steps, chat thread mock, and CTAs representing the client ↔ agent workflow.
- **Data highlights** – placeholder metrics plus a feature/news table that references backend data endpoints conceptually.
- **Backtest insights** – cards summarizing backtest KPIs and an adjacent news feed mock.
- **Dashboard page (`/dashboard.html`)** – now fetches cached prices/features/news from the Flask backend (set `VITE_API_BASE`, defaults to `http://localhost:8000`) to plot price + indicator charts and populate the strategies table.

## Run locally
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Or run inside Docker (requires a backend API running somewhere and optionally a `VITE_API_BASE` override):

```bash
# from repo root
VITE_API_BASE=http://localhost:8000 docker compose -f docker-compose.frontend.yml up
```
Set `VITE_API_BASE` in `.env` (or export it) to point at the backend, e.g.:

```
VITE_API_BASE=http://localhost:8000
```

## Next steps (frontend)
- Wire dashboard and workspace views to real APIs (strategies list/detail, backtest runs/results, news overlays).
- Replace static metrics with live data from backend endpoints and connect CTAs to real flows.
- Add routing between home and dashboard via a client-side router instead of a second HTML entrypoint.
- Improve accessibility and empty/loading/error states as data becomes dynamic.

## Backend: what exists today (from `backend/app.py`)
- Market/feature endpoints: `GET /data/prices`, `POST /features`.
- Cache reads: `GET /cache/prices`, `/cache/features`, `/cache/news`, `/cache/trades`.
- Maintenance: `POST /refresh` to backfill/refresh cached prices/features (and optional news/trades).
- Health: `GET /health`.

## Backend APIs still needed to fully power the frontend
The UI presently uses static data because these services are absent:
1. **Strategies + agents**: CRUD for strategies (`/strategies`), agent definitions, and assignments to runs.
2. **Backtests**: create/trigger runs, fetch results + time series, and surface historical runs for the dashboard/table.
3. **Chat + collaboration**: persistence/search for conversation threads and message posting endpoints.
4. **Notifications/events**: feed for alerts (e.g., backtest completions, signal triggers, news flags).
5. **Auth + workspace scoping**: user/session auth, tenant/workspace boundaries, and RBAC around strategies/data.
6. **Agent middleware bridge**: orchestration entrypoints for multi-agent tasks (signal generation, routing, guardrails).

## Relationship to the Strategy submodule
- Once the dedicated Strategy service (see `strategy/README.md`) ships, wire dashboard/workspace calls to its APIs for
  listing strategies, fetching versions, and requesting validation/refinements.
- Coordinate on shared types (strategy DSL, version metadata) via a generated client so UI state stays in sync with the
  backend + strategy services.
- Expect new endpoints for combined price/indicator/signal series that will let the dashboard render a strategy in one
  request; update the data fetching hooks accordingly.
