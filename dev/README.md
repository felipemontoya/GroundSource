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

From the repository root:

```
cp dev/.env.example dev/.env    # once; then put the OpenAI key in it
make dev-start                  # or: make dev start
make dev-stop                   # or: make dev stop
```

`make dev-start` builds, starts, and returns once every service is healthy.
`make dev-stop` removes the containers but keeps the volumes, so ingested
documents and their embeddings survive a restart. The Makefile is only a
shortcut; from this directory the equivalent is `docker compose up -d
--build --wait` and `docker compose down`.

`.env` is read automatically by Compose and is git-ignored. The stack starts
without a key; what needs one is embedding and answer generation.

Three services come up, and a fourth on demand:

| Service | Image / build | Host port | What it is |
|---|---|---|---|
| `db` | `pgvector/pgvector:pg17` | 5432 | PostgreSQL with `pgvector` and `pg_trgm` |
| `api` | `../api/Dockerfile` | 8000 | Django 5 on ASGI (uvicorn), auto-reloading |
| `web` | `../pages/web/Dockerfile` (`dev` target) | 5173 | Vite dev server for the reference page |
| `tools` | `../api/Dockerfile` | — | One-off commands that write into the source tree. Profile `tools`, not started by `up`. |

Then:

- <http://localhost:5173> — the page.
- <http://localhost:8000/health> — database and `pgvector` health.
- <http://localhost:8000/sources> — what is ingested, and whether a provider
  is configured.

The page reaches the API through the dev server's `/api` proxy rather than
cross-origin. That is deliberate: it keeps a reverse proxy in the local path,
which is where SSE buffering problems show up, and it means the API does not
need CORS until a build is hosted on its own origin.

## Loading a document

Ingestion is free and needs no API key; embedding costs money and does.
They are separate commands for that reason.

```
# Parse, anchor and index. Deterministic, re-runnable, no key needed.
docker compose exec api python manage.py ingest_source \
    "/sources/<file>.pdf" --slug <handle> --language english

# Prove the chain: every unit's indexed text still matches its slice.
docker compose exec api python manage.py verify_anchors <handle>

# Embed for semantic retrieval. Needs OPENAI_API_KEY.
docker compose exec api python manage.py embed_source <handle>
```

`sources/` is mounted read-only at `/sources`. Use `--language spanish` for
Spanish documents: it selects the PostgreSQL text search configuration, and
it is per source because the test bed is English and the target document is
not.

`--edition` names which typesetting a file is — "JEP, 2018", "Cancillería,
24 Nov 2016". Two editions of one text are two sources on purpose: they
paginate differently, so a citation's page number only means something under
the edition that produced it. The page keeps a separate conversation per
document for the same reason.

## Asking it things

<http://localhost:5173> once a document is loaded. Or directly:

```
curl -X POST localhost:8000/sources/<handle>/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "..."}'
```

The stack is useful at every level of configuration. With no key at all,
questions return the passages that match lexically. With a key but no
embeddings, matching is lexical and the answer is generated. With both,
retrieval is hybrid. Each state is reported rather than hidden.

## Generating migrations

The `api` service mounts the code read-only — it runs the source, it does
not edit it — so anything that writes into the tree uses the `tools`
profile instead:

```
docker compose run --rm tools python manage.py makemigrations
```

## What this is not yet

No conversation history, no streaming, no rate limiting, no spend cap. All
four are Phase 1 in `../docs/planning/initial-thinking.md`, and the last two
have to exist before anything is publicly reachable.

## Resetting

```
docker compose down -v      # drops the database volume and node_modules
```

The `db` init scripts in `postgres/initdb/` run only on an empty data
directory, so changing them requires this reset to take effect.
