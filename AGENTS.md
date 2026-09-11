# AGENTS.md

Working agreements for AI agents (and humans) contributing to GroundSource.
Read `README.md` first for what the project is; this file covers how to work
in it.

## The one thing that matters

GroundSource exists to show people what a document actually says. A feature
that makes answers smoother at the cost of traceability is a regression, not
an improvement. When a trade-off appears between fluency and provenance,
provenance wins.

Concretely, code in this repo must preserve the chain:

```
original bytes → character offsets → structural anchor → quoted span → answer
```

Any step that drops or blurs a link in that chain is a bug, however good the
output looks.

## Vocabulary

Use these terms consistently in code, schemas, and prose.

- **Source** — the immutable original file as ingested, with checksum.
- **Document** — the parsed representation of a source: a tree of units.
- **Unit** — an addressable structural node: section, article, clause,
  paragraph, list item, table, footnote.
- **Anchor** — a stable identifier for a unit (path plus character range
  into the source's canonical text). Anchors are part of the public API and
  must not change silently between runs.
- **Span** — a contiguous run of verbatim source text, identified by anchor.
- **Citation** — a span plus the link that resolves it in the original.
- **Preparation** — the offline passes that derive summaries, terms,
  cross-references, and embeddings from a document.
- **Grounded answer** — an answer in which every claim about the document is
  backed by at least one citation.

## Invariants

1. **The source is immutable.** Never rewrite, normalize in place, or
   "clean" an ingested source. Normalization produces a separate canonical
   text with an offset map back to the original.
2. **Offsets are sacred.** Any transformation of text must either preserve
   offsets or carry an explicit mapping. Silent trimming, unicode
   normalization, or whitespace collapsing that breaks offsets is a defect.
3. **Derived data is regenerable.** Every prepared artifact records the
   source checksum, the pipeline version, and the model/prompt version that
   produced it. Nothing derived is hand-edited.
4. **No invented text.** Quoted spans are sliced from the source
   programmatically, never produced by a model. Model output may select
   anchors; it may not author quotations.
5. **Abstention is a valid answer.** Retrieval that finds nothing relevant
   must surface that, not degrade into unanchored generation.
6. **Neutrality by construction.** No component ranks, scores, or labels
   political positions. Retrieval and presentation order are driven by
   textual relevance and document structure, not by stance.
7. **Deterministic where it can be.** Parsing, anchoring, and slicing are
   deterministic and tested as such. Nondeterminism is confined to the
   model-backed passes and the chat agent.

## Stack

Settled:

- **Backend:** Python + Django.
- **Database:** PostgreSQL. It also holds the structural tree, spans, and
  preparation artifacts; vector storage is expected to live there too
  (pgvector) unless a measured reason forces a separate index.
- **Frontend:** not settled. The working assumption is a statically hosted
  page built with a modern JavaScript stack, talking to the Django API over
  HTTP. Until it is chosen, the backend must not assume a server-rendered
  frontend: the API is the contract, and anything the UI needs is available
  through it.

Consequences for code in this repo:

- Long-running preparation passes run out of band (management commands or a
  task queue), never inside a request/response cycle.
- Migrations are checked in and are never edited after being applied
  anywhere shared.
- The API is CORS-aware and token/session-authenticated in a way a static
  origin can use.

## Contributing agents: ground rules

- **Commits are allowed on request, and only on request.** For this project
  the repository owner works largely through Clo rather than committing
  directly, so Clo may create commits — but only when told to in that
  message or an explicit standing instruction. Absent that, leave changes in
  the working tree and report them. Never commit as a cleanup step, never
  amend or rebase shared history unasked, and never push unless asked.
- **Do not add dependencies casually.** This project will be public and
  audited; each dependency needs a reason.
- **Do not silently widen scope.** If a task reveals adjacent work, finish
  the task and report the adjacent work.
- **Update this file** when an invariant or a settled decision changes — and
  say so in the summary of the change.

## Open decisions

Do not treat these as settled; raise them rather than picking silently.

- Repository layout: how the pipeline stages map onto Django apps and
  packages, and where frontend code lives.
- Coding conventions: testing strategy, prompt management, API schema style,
  fixtures, tooling.
- The runtime agent's concrete behavior rules — how grounded answers are
  composed, formatted, and presented — beyond the contract in `README.md`.
- Frontend framework and hosting target.
- Embedding and chat model providers.
- Task queue for preparation passes (Celery, RQ, or Django-native).
- Link format for resolving anchors in the original document (page + offset
  for PDFs, fragment identifiers for HTML).
- Multi-document / corpus support beyond the single-document case.
- License.
