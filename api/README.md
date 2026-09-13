# api

The Django backend: the whole server-side system, not only its HTTP surface.
Ingestion, parsing, preparation passes, retrieval, the grounding agent, and
the API that `../pages/` calls all live here.

Stack: Python + Django + PostgreSQL. See `../AGENTS.md` for the invariants
this code must preserve — above all the chain from original bytes through
character offsets and anchors to the quoted spans an answer is built from.

## What exists today

Scaffolding. A Django 5 project served over ASGI by uvicorn, talking to
PostgreSQL with `pgvector`, and two endpoints:

- `GET /` — identifies the service and says what is not built yet.
- `GET /health` — checks the database and proves `pgvector` computes a
  distance, not merely that the extension row exists. `200` when both pass,
  `503` with the same body shape when either fails.

There are no Django apps yet, on purpose: how pipeline stages map onto apps
and packages is an open decision in `../AGENTS.md`, and inventing a layout
to hold one health view would pre-empt it. `groundsource/urls.py` is meant
to grow by including app URLconfs once that decision is made.

## Running it

Through the development environment, which is the supported path:

```
cd ../dev && docker compose up
```

The container applies migrations on start, so the stack comes up in one
command. Set `RUN_MIGRATIONS=0` to skip that — a deployment runs migrations
as a separate, observable step rather than racing replicas against each
other.

## Configuration

Read from the environment, with the same variable names locally and in
deployment (`../dev/.env.example` lists them):
`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`,
`POSTGRES_PORT`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`,
`DJANGO_ALLOWED_HOSTS`, `DJANGO_LOG_LEVEL`.

The development secret key is refused when `DJANGO_DEBUG` is off, so a
deployment cannot silently run on a key that is published in this
repository.

## Not here yet

CORS. The page reaches the API through its dev server's proxy, so nothing
is cross-origin locally. A static build hosted on its own origin needs CORS
before it works, and that is a decision about allowed origins rather than a
line of configuration to add now.
