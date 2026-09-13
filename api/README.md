# api

The Django backend: the whole server-side system, not only its HTTP surface.
Ingestion, parsing, preparation passes, retrieval, the grounding agent, and
the API that `../pages/` calls all live here.

Stack: Python + Django + PostgreSQL. See `../AGENTS.md` for the invariants
this code must preserve — above all the chain from original bytes through
character offsets and anchors to the quoted spans an answer is built from.

## What exists today

A Django 5 project on ASGI over PostgreSQL with `pgvector`, and one app,
`grounding`, holding the Phase 0 pipeline end to end.

| Module | Stage |
|---|---|
| `extraction.py` | PDF bytes → canonical text plus a page map. The stage where the offset invariant lives or dies. |
| `parsing.py` | Canonical text → a tree of units, delimited by the document's own numbering, never by size. |
| `models.py` | The chain as tables: `Source`, `Page`, `Unit`, `Embedding`. |
| `spans.py` | The only place a quotation is produced. Slices from canonical text; rejects a range that does not resolve. |
| `retrieval.py` | Dense plus lexical, fused by reciprocal rank. |
| `llm.py` | The provider seam. Every call that leaves the machine goes through it. |
| `answering.py` | Retrieved units → a grounded answer, with the contract checked in code. |

Endpoints:

- `GET /` — identifies the service.
- `GET /health` — checks the database and proves `pgvector` computes a
  distance, not merely that the extension row exists. `200` when both pass,
  `503` with the same body shape when either fails.
- `GET /sources` — what is ingested, and whether a provider is configured.
- `GET /sources/<slug>/outline` — the document's own headings.
- `POST /sources/<slug>/ask` — `{"question": "..."}` in, a grounded answer or
  an abstention out.

Commands: `ingest_source`, `verify_anchors`, `embed_source`. The first two
are free and need no key; the third costs money. That split is deliberate —
see `../dev/README.md`.

One app is not the answer to the open decision in `../AGENTS.md` about how
pipeline stages map onto apps. It is what a proof of concept needs, and
splitting it later is a migration rather than a rewrite.

## How the grounding contract is enforced

Not by asking the model nicely. The JSON schema it must fill has slots for
unit ids and offset ranges and **no slot for quoted text**, so it selects
anchors and cannot author quotations. Every range it returns is sliced out
of the database by `spans.quote_within`, which rejects a range overflowing
its unit rather than clamping it. A claim whose citations all fail is marked
unsupported; an answer with no supported claims becomes an abstention.

`manage.py verify_anchors` is the check that the chain has not silently
broken: it re-slices every unit and compares against the copy the full-text
index scores. It is cheap, needs no key, and belongs in CI.

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
`DJANGO_ALLOWED_HOSTS`, `DJANGO_LOG_LEVEL`, `OPENAI_API_KEY`,
`EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, `CHAT_MODEL`,
`CHAT_MAX_OUTPUT_TOKENS`, `PIPELINE_VERSION`, `SOURCES_DIR`.

A missing `OPENAI_API_KEY` is not a startup error. Ingestion and lexical
retrieval work without one, and the API reports the degraded state instead
of failing.

The development secret key is refused when `DJANGO_DEBUG` is off, so a
deployment cannot silently run on a key that is published in this
repository.

## Not here yet

CORS. The page reaches the API through its dev server's proxy, so nothing
is cross-origin locally. A static build hosted on its own origin needs CORS
before it works, and that is a decision about allowed origins rather than a
line of configuration to add now.
