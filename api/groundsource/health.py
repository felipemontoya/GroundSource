"""Liveness and readiness for the proof-of-concept stack.

The point of this endpoint is to prove the stack is wired end to end: the
page reaches the API, the API reaches PostgreSQL, and the database really
does have `pgvector` loaded rather than merely being reachable. It checks
the extension by running a distance operation, because an extension row in
a catalogue table is weaker evidence than a vector that actually computes.
"""

import json

from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse

SERVICE = "groundsource-api"


def _check_database() -> dict:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version()")
        (version,) = cursor.fetchone()
    return {"status": "ok", "server": version.split(" on ")[0]}


def _check_pgvector() -> dict:
    with connection.cursor() as cursor:
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        row = cursor.fetchone()
        if row is None:
            return {"status": "error", "detail": "extension 'vector' is not installed"}
        # Exercise the type and an operator, not just the catalogue entry.
        cursor.execute("SELECT '[1,0]'::vector <-> '[0,1]'::vector")
        (distance,) = cursor.fetchone()
    return {"status": "ok", "version": row[0], "probe_l2_distance": float(distance)}


def health(request: HttpRequest) -> JsonResponse:
    checks = {}
    for name, probe in (("database", _check_database), ("pgvector", _check_pgvector)):
        try:
            checks[name] = probe()
        except Exception as exc:  # surfaced to the caller, not swallowed
            checks[name] = {"status": "error", "detail": f"{type(exc).__name__}: {exc}"}

    ok = all(check["status"] == "ok" for check in checks.values())
    payload = {"status": "ok" if ok else "error", "service": SERVICE, "checks": checks}
    return JsonResponse(payload, status=200 if ok else 503, json_dumps_params={"indent": 2})


def root(request: HttpRequest) -> HttpResponse:
    """Identify the service. No document endpoints exist yet, by design."""
    payload = {
        "service": SERVICE,
        "status": "skeleton",
        "detail": "Stack scaffolding only. No ingestion, retrieval, or chat endpoints yet.",
        "endpoints": {"health": "/health"},
    }
    return HttpResponse(
        json.dumps(payload, indent=2) + "\n",
        content_type="application/json",
    )
