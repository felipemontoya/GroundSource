# api

The Django backend: the whole server-side system, not only its HTTP surface.
Ingestion, parsing, preparation passes, retrieval, the grounding agent, and
the API that `../pages/` calls all live here.

Stack: Python + Django + PostgreSQL. See `../AGENTS.md` for the invariants
this code must preserve — above all the chain from original bytes through
character offsets and anchors to the quoted spans an answer is built from.
