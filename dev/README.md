# dev

A running development environment: Docker Compose orchestration for local
work — Postgres with pgvector, the Django backend, a page dev server — plus
seed data and the conveniences that make the stack start with one command.

Each service's Dockerfile lives next to the code it builds (`../api/Dockerfile`).
This directory holds orchestration and seed data only, so that `../ops/` can
reference the same images instead of maintaining a second definition.

Kept separate from `../ops/` so that production concerns and local
conveniences do not leak into each other. The environment contract, though,
is meant to be the same in both: the same service names, the same
configuration variables, ideally the same images.

Local state produced here (database volumes, caches, generated artifacts) is
disposable and is not committed.

## Starting it

```
cp .env.example .env      # optional; the defaults in compose.yaml match it
docker compose up --build
```

Three services come up:

| Service | Image / build | Host port | What it is |
|---|---|---|---|
| `db` | `pgvector/pgvector:pg17` | 5432 | PostgreSQL with `pgvector` and `pg_trgm` |
| `api` | `../api/Dockerfile` | 8000 | Django 5 on ASGI (uvicorn), auto-reloading |
| `web` | `../pages/web/Dockerfile` (`dev` target) | 5173 | Vite dev server for the reference page |

Then:

- <http://localhost:5173> — the page, which reports the backend's health.
- <http://localhost:8000/health> — the same report directly from the API.

The page reaches the API through the dev server's `/api` proxy rather than
cross-origin. That is deliberate: it keeps a reverse proxy in the local path,
which is where SSE buffering problems show up, and it means the API does not
need CORS until a build is hosted on its own origin.

## What this is not yet

No ingestion, no retrieval, no chat. The stack exists; the pipeline does not.
The health endpoint checks that PostgreSQL is reachable *and* that `pgvector`
computes a distance, so a green page means the substrate the pipeline needs
is actually there.

## Resetting

```
docker compose down -v      # drops the database volume and node_modules
```

The `db` init scripts in `postgres/initdb/` run only on an empty data
directory, so changing them requires this reset to take effect.
