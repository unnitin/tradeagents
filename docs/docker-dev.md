## Running the backend in Docker (dev)

This project now ships with a dev-only Compose file so you can run the backend API inside Docker while keeping the source code and SQLite database on the host.

### Prerequisites

- Docker Desktop (or compatible engine) installed and running.
- Existing `data/` directory in the repo root (create it with `mkdir -p data`). SQLite will create `data.db` and WAL files inside this folder automatically.

### Start the API

```bash
docker compose -f docker-compose.dev.yml up --build
```

This command:

- Builds the existing `Dockerfile`.
- Mounts `./backend` into `/app/backend` for live code edits.
- Mounts `./data` into `/app/data` so the container stores SQLite artifacts in a dedicated directory shared with the host.
- Exposes the API on `http://localhost:8000`.

Stop the service with `Ctrl+C` (or `docker compose ... down`).

### Running tests inside the container

```bash
docker compose -f docker-compose.dev.yml run --rm backend pytest
```

### Running automation helpers (e.g., backfill)

```bash
docker compose -f docker-compose.dev.yml exec backend python -m backend.automation seed_from_config
```

### Notes on prod parity

- The same Docker image can be deployed to AWS Fargate (or similar) by pointing `DATA_DB_PATH` to an RDS connection/DSN instead of the mounted SQLite file.
- Remove the bind mounts and supply production environment variables/secrets through your orchestrator to reproduce a prod setup.
