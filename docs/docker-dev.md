## Running the backend in Docker (dev)

Use `docker-compose.backend.yml` to run only the Flask backend/API inside Docker while keeping source code and SQLite data on the host.

### Prerequisites

- Docker Desktop (or compatible engine) installed and running.
- Existing `data/` directory in the repo root (create it with `mkdir -p data`). SQLite will create `data.db` and WAL files inside this folder automatically.

### Start the backend

```bash
docker compose -f docker-compose.backend.yml up --build
```

This command:

- Builds the backend Dockerfile.
- Mounts `./backend` into `/app/backend` for live code edits.
- Mounts `./data` into `/app/data` so the container stores SQLite artifacts in a dedicated directory shared with the host.
- Exposes the API on `http://localhost:8000`.

Stop the service with `Ctrl+C` (or `docker compose ... down`).

## Running the frontend in Docker (dev)

Use `docker-compose.frontend.yml` when you want the Vite dev server running inside Docker (e.g., to match production tooling) without coupling it to the backend container.

### Start the frontend

```bash
VITE_API_BASE=http://localhost:8000 docker compose -f docker-compose.frontend.yml up --build
```

This command:

- Builds `frontend/Dockerfile`.
- Mounts `./frontend` into `/app` (with an anonymous `node_modules` volume) so edits instantly reflect inside the container.
- Exposes the Vite dev server on `http://localhost:5173`. Configure `VITE_API_BASE` to whichever backend URL you need (default falls back to `http://localhost:8000`).

Stop it with `Ctrl+C` (or `docker compose -f docker-compose.frontend.yml down`).

### Running tests inside the container

```bash
docker compose -f docker-compose.backend.yml run --rm backend pytest
```

### Running automation helpers (e.g., backfill)

```bash
docker compose -f docker-compose.backend.yml exec backend python -m backend.automation seed_from_config
```

### Notes on prod parity

- The same Docker image can be deployed to AWS Fargate (or similar) by pointing `DATA_DB_PATH` to an RDS connection/DSN instead of the mounted SQLite file.
- Remove the bind mounts and supply production environment variables/secrets through your orchestrator to reproduce a prod setup.
