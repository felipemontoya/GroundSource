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
