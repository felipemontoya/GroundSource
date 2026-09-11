# ADR-0001: Monorepo layout

- **Status:** Proposed
- **Date:** 2026-09-10

## Context

GroundSource spans several kinds of work that have to stay in step: a Django
backend that ingests and prepares documents and serves a grounding API, one
or more statically hosted front ends, the original source documents
themselves, deployment and monitoring configuration, and a local development
environment. The project is small and single-maintainer today, and is
intended to become public.

The system's central promise is traceability from an answer back to the
original bytes of a document. That promise spans components: a change to
parsing, to the API's citation schema, and to how a page renders a quotation
are one logical change. Splitting those into separately versioned
repositories would mean that promise is only ever verified across repository
boundaries.

## Decision

One repository, organized as a monorepo:

```
docs/adrs/      immutable architecture decision records
docs/planning/  living design and planning documents
api/            the Django backend, in full
pages/          frontend code, one subdirectory per page
sources/        the original documents, as ingested
ops/            deployment, infrastructure, monitoring
dev/            local development environment
```

`docs/` is split because its two halves have opposite rules: ADRs are
immutable once accepted and are superseded rather than edited; planning
documents are expected to change and are kept current with the code.

`pages/` is plural from the start, though only one page exists, so that
adding a second front end never requires relocating the first.

`sources/` holds original documents in the repository for now, accepting
that they may later move to object storage or the database.

## Alternatives considered

- **Separate repositories per component.** Rejected: the grounding chain
  crosses component boundaries, and coordinating it across repositories adds
  synchronization cost with no benefit at this size.
- **A single Python package with the frontend nested inside it.** Rejected:
  it makes the front end look like a Django concern, which contradicts the
  intent that the API is the only contract between them.
- **`frontend/` instead of `pages/`.** Rejected: singular naming would have
  to be undone as soon as a second front end appears.
- **`backend/` instead of `api/`.** Considered, and the weaker point of this
  layout: `api/` will hold ingestion, parsing, and preparation code that is
  not an API in any sense. `api/` was kept because it names the thing the
  rest of the repository actually talks to.
- **One combined `docs/` directory.** Rejected: immutable and living
  documents kept side by side blur into each other, and ADRs get edited.

## Consequences

- One checkout, one history, one place to look; cross-cutting changes land
  as a single commit.
- Tooling must be path-aware: CI needs path filters to avoid running the
  Python suite for a page-only change, and there is no single dependency
  manifest for the repository.
- Storing sources in git means the history carries binary documents and
  grows permanently; if documents get large or numerous this becomes a
  migration to Git LFS or external storage, and only originals — never
  derived artifacts — are ever committed.
- Publishing the repository publishes the source documents with it, so each
  one must be checked for redistribution rights before it is added.
- `dev/` and `ops/` describe the same system twice and will drift unless
  their shared pieces are genuinely shared.
