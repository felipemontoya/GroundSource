"""Finding the units a question might be answered from.

Hybrid, not vector-only: dense retrieval finds paraphrase, lexical
retrieval finds the exact term a legal document turns on. A question about
"RTO" has to reach the clause that says "RTO" even when nothing about the
embedding of that clause is close to the embedding of the question.

The two lists are fused by Reciprocal Rank Fusion, which combines rankings
without needing the two scores to be comparable — cosine distance and
`ts_rank_cd` are not on the same scale and no amount of weighting makes them
so.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.db import connection

from . import llm
from .models import Source, Unit

# The constant from the original RRF paper. Large enough that the top of one
# list cannot single-handedly outvote a consistent showing in both.
RRF_K = 60


@dataclass
class Candidate:
    unit: Unit
    dense_rank: int | None = None
    lexical_rank: int | None = None
    score: float = 0.0

    @property
    def why(self) -> str:
        if self.dense_rank is not None and self.lexical_rank is not None:
            return "both"
        if self.dense_rank is not None:
            return "semantic"
        return "lexical"


@dataclass
class Retrieval:
    candidates: list[Candidate]
    dense_used: bool
    lexical_used: bool
    notes: list[str]

    @property
    def units(self) -> list[Unit]:
        return [candidate.unit for candidate in self.candidates]


def _lexical(source: Source, query: str, limit: int) -> list[int]:
    """Rank unit ids by full-text relevance, in the source's own language.

    The question's words are ORed, not ANDed. `websearch_to_tsquery` and
    `plainto_tsquery` both require every term to be present, which is right
    for a search box and wrong for retrieval: "What is the recovery time
    objective?" then matches nothing, because no single clause contains
    "recovery" and "time" and "objective" together — while the clause that
    answers it contains two of the three. Ranking sorts out which partial
    match is best; requiring all of them never gets the chance.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH q AS (
                SELECT to_tsquery(
                    %s::regconfig,
                    nullif(
                        array_to_string(
                            tsvector_to_array(to_tsvector(%s::regconfig, %s)), ' | '
                        ),
                        ''
                    )
                ) AS query
            )
            SELECT u.id
            FROM grounding_unit u, q
            WHERE u.source_id = %s
              AND q.query IS NOT NULL
              AND u.search_vector @@ q.query
            ORDER BY ts_rank_cd(u.search_vector, q.query) DESC, u.ordinal ASC
            LIMIT %s
            """,
            [source.language, source.language, query, source.pk, limit],
        )
        return [row[0] for row in cursor.fetchall()]


def _dense(source: Source, query: str, limit: int) -> list[int]:
    """Rank unit ids by cosine distance from the question's embedding."""
    (vector,) = llm.embed([query])
    literal = "[" + ",".join(f"{value:.7f}" for value in vector) + "]"

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT u.id
            FROM grounding_embedding e
            JOIN grounding_unit u ON u.id = e.unit_id
            WHERE u.source_id = %s AND e.model = %s
            ORDER BY e.vector <=> %s::vector
            LIMIT %s
            """,
            [source.pk, settings.EMBEDDING_MODEL, literal, limit],
        )
        return [row[0] for row in cursor.fetchall()]


def retrieve(source: Source, query: str, *, top_k: int | None = None) -> Retrieval:
    """Return the units most likely to contain the answer, best first."""
    top_k = top_k or settings.RETRIEVAL_TOP_K
    limit = settings.RETRIEVAL_CANDIDATES
    notes: list[str] = []

    lexical_ids = _lexical(source, query, limit)
    lexical_used = True

    dense_ids: list[int] = []
    dense_used = False
    if llm.is_configured():
        try:
            dense_ids = _dense(source, query, limit)
            dense_used = True
        except llm.ProviderUnavailable as exc:
            notes.append(f"Semantic retrieval unavailable, lexical only: {exc}")
    else:
        notes.append("OPENAI_API_KEY is not set: lexical retrieval only, no semantic matching.")

    if dense_used and not dense_ids:
        notes.append("No embeddings stored for this source: run `manage.py embed_source`.")

    scores: dict[int, Candidate] = {}
    units = {unit.pk: unit for unit in Unit.objects.filter(pk__in=set(dense_ids) | set(lexical_ids))}

    for rank, unit_id in enumerate(dense_ids, start=1):
        candidate = scores.setdefault(unit_id, Candidate(unit=units[unit_id]))
        candidate.dense_rank = rank
        candidate.score += 1 / (RRF_K + rank)

    for rank, unit_id in enumerate(lexical_ids, start=1):
        candidate = scores.setdefault(unit_id, Candidate(unit=units[unit_id]))
        candidate.lexical_rank = rank
        candidate.score += 1 / (RRF_K + rank)

    ranked = sorted(scores.values(), key=lambda c: (-c.score, c.unit.ordinal))

    if not ranked:
        notes.append("Nothing in this document matched the question.")

    return Retrieval(
        candidates=ranked[:top_k],
        dense_used=dense_used,
        lexical_used=lexical_used,
        notes=notes,
    )


def with_neighbours(source: Source, units: list[Unit]) -> list[Unit]:
    """Each unit plus the one before and after it, in document order.

    The grounding contract asks that a quoted clause arrive with enough
    surrounding text to check whether the quote survives its context. A
    retrieved paragraph without its own heading is exactly the case where it
    does not.
    """
    wanted: set[int] = set()
    for unit in units:
        wanted.update({unit.ordinal - 1, unit.ordinal, unit.ordinal + 1})
        if unit.parent_id:
            wanted.add(unit.parent.ordinal)

    return list(
        Unit.objects.filter(source=source, ordinal__in=wanted).order_by("ordinal")
    )
