"""Retrieved units → a grounded answer, with the contract enforced in code.

The model's job here is narrow: read the retrieved units and decide which
ranges of them support which claim. It never writes a quotation. The schema
it must answer in has no field for quoted text — only unit ids and offset
ranges relative to a unit's start — and every range it returns is sliced
from the database by `spans.quote_within` before a reader sees it.

Everything the model returns is then checked:

- a citation naming a unit that was not retrieved is dropped;
- a range that overflows its unit is dropped;
- a claim left with no surviving citation is marked unsupported;
- an answer with no surviving claims becomes an abstention.

That last step is the one that matters. Invariant 5 says abstention is a
valid answer, so the failure mode of this function is silence, not an
unanchored paragraph.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from . import llm, retrieval, spans
from .models import Source, Unit

logger = logging.getLogger(__name__)

INSTRUCTIONS = """\
You answer questions about one document, and only from the numbered extracts \
you are given. You never use outside knowledge about the subject.

You do not write quotations. For every claim you make, you identify which \
extract supports it and the character range within that extract that a \
reader should look at. The system slices that range out of the document \
itself; if you describe text that is not there, the claim is discarded.

Rules:
- Every claim must carry at least one citation.
- Offsets are relative to the start of the extract, counting from 0, and \
must fall inside the extract's stated length.
- Choose ranges that are a sentence or more: enough that a reader can tell \
whether the quotation survives its context.
- If the extracts do not answer the question, set abstained to true and say \
what is missing. Do not answer from general knowledge.
- Mark a claim as "interpretation" when it combines or reads between \
extracts rather than restating one. Mark it "quotation" when it restates \
what a single extract says.
- Where the text genuinely supports more than one reading, give both as \
separate claims rather than choosing.
- Write your statements in the same language as the question. The quotations \
are sliced from the document and are never translated, so a statement in one \
language may well sit above a quotation in another; that is correct.
"""

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["abstained", "abstention_reason", "claims"],
    "properties": {
        "abstained": {"type": "boolean"},
        "abstention_reason": {
            "type": ["string", "null"],
            "description": "What the document does not say. Null unless abstained.",
        },
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["statement", "kind", "citations"],
                "properties": {
                    "statement": {"type": "string"},
                    "kind": {"type": "string", "enum": ["quotation", "interpretation"]},
                    "citations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["extract", "start", "end"],
                            "properties": {
                                "extract": {
                                    "type": "integer",
                                    "description": "The extract number as labelled in the prompt.",
                                },
                                "start": {"type": "integer"},
                                "end": {"type": "integer"},
                            },
                        },
                    },
                },
            },
        },
    },
}


@dataclass
class Claim:
    statement: str
    kind: str
    quotes: list[spans.Quote] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)

    @property
    def supported(self) -> bool:
        return bool(self.quotes)

    def as_dict(self) -> dict:
        return {
            "statement": self.statement,
            "kind": self.kind,
            "supported": self.supported,
            "citations": [quote.as_dict() for quote in self.quotes],
        }


@dataclass
class Answer:
    source: Source
    question: str
    abstained: bool
    abstention_reason: str | None
    claims: list[Claim]
    retrieved: list[Unit]
    notes: list[str]
    model: str | None = None
    usage: dict | None = None

    def as_dict(self) -> dict:
        return {
            # Identity of the document this answer came out of. An answer
            # that does not name its own edition can be shown under the
            # wrong one, and page numbers belong to an edition — so this
            # travels with every response rather than being inferred from
            # whatever the page happens to have selected.
            "source": {
                "slug": self.source.slug,
                "title": self.source.title,
                "edition": self.source.edition,
                "sha256": self.source.sha256,
                "pages": self.source.page_count,
            },
            "question": self.question,
            "abstained": self.abstained,
            "abstention_reason": self.abstention_reason,
            "claims": [claim.as_dict() for claim in self.claims],
            "retrieved": [
                {
                    **unit.anchor,
                    "kind": unit.kind,
                    "heading": unit.heading,
                    "preview": unit.text[:200],
                }
                for unit in self.retrieved
            ],
            "notes": self.notes,
            "model": self.model,
            "usage": self.usage,
        }


def _render_extracts(source: Source, units: list[Unit]) -> str:
    """Lay out the retrieved units for the model, with lengths it must respect."""
    blocks = []
    for number, unit in enumerate(units, start=1):
        text = source.slice(unit.start_offset, unit.end_offset)
        label = unit.path or f"unit {unit.pk}"
        page = unit.page_start if unit.page_start == unit.page_end else f"{unit.page_start}–{unit.page_end}"
        heading = f" — {unit.heading}" if unit.heading else ""
        blocks.append(
            f"[extract {number}] section {label}{heading} (page {page}, "
            f"length {len(text)} characters)\n{text}"
        )
    return "\n\n".join(blocks)


def answer_question(source: Source, question: str, *, top_k: int | None = None) -> Answer:
    """Answer from the document, or decline."""
    found = retrieval.retrieve(source, question, top_k=top_k)
    notes = list(found.notes)
    units = found.units

    if not units:
        return Answer(
            source=source,
            question=question,
            abstained=True,
            abstention_reason="Nothing in this document matched the question.",
            claims=[],
            retrieved=[],
            notes=notes,
        )

    if not llm.is_configured():
        # Still useful without a key: the reader gets the passages and can
        # read them, which is closer to the point of this tool than a
        # generated summary would be anyway.
        notes.append("No answer was generated. The extracts below are the raw retrieval result.")
        return Answer(
            source=source,
            question=question,
            abstained=True,
            abstention_reason="No model provider is configured, so no answer was composed.",
            claims=[],
            retrieved=units,
            notes=notes,
        )

    prompt = f"Question: {question}\n\n{_render_extracts(source, units)}"

    try:
        completion = llm.complete_json(
            instructions=INSTRUCTIONS, prompt=prompt, schema=SCHEMA
        )
    except llm.ProviderUnavailable as exc:
        notes.append(f"Answer generation failed: {exc}")
        return Answer(
            source=source,
            question=question,
            abstained=True,
            abstention_reason="The model provider could not be reached.",
            claims=[],
            retrieved=units,
            notes=notes,
        )

    claims, validation_notes = _validate(source, units, completion.payload)
    notes.extend(validation_notes)

    abstained = bool(completion.payload.get("abstained")) or not any(c.supported for c in claims)
    reason = completion.payload.get("abstention_reason")
    if abstained and not reason:
        reason = "No claim survived citation checking, so nothing here is grounded."

    return Answer(
        source=source,
        question=question,
        abstained=abstained,
        abstention_reason=reason if abstained else None,
        claims=[claim for claim in claims if claim.supported or not abstained],
        retrieved=units,
        notes=notes,
        model=completion.model,
        usage={
            "input_tokens": completion.input_tokens,
            "output_tokens": completion.output_tokens,
        },
    )


def _validate(source: Source, units: list[Unit], payload: dict) -> tuple[list[Claim], list[str]]:
    """Turn the model's selections into quotes, discarding what does not resolve."""
    by_number = {number: unit for number, unit in enumerate(units, start=1)}
    claims: list[Claim] = []
    notes: list[str] = []

    for raw in payload.get("claims") or []:
        claim = Claim(
            statement=str(raw.get("statement", "")).strip(),
            kind=raw.get("kind") if raw.get("kind") in {"quotation", "interpretation"} else "interpretation",
        )
        if not claim.statement:
            continue

        for citation in raw.get("citations") or []:
            unit = by_number.get(citation.get("extract"))
            if unit is None:
                claim.dropped.append(f"extract {citation.get('extract')} was not retrieved")
                continue
            try:
                claim.quotes.append(
                    spans.quote_within(source, unit, int(citation["start"]), int(citation["end"]))
                )
            except (spans.SpanError, KeyError, TypeError, ValueError) as exc:
                claim.dropped.append(f"extract {citation.get('extract')}: {exc}")

        if claim.dropped:
            notes.append(
                f"Dropped {len(claim.dropped)} citation(s) that did not resolve: "
                + "; ".join(claim.dropped)
            )
        claims.append(claim)

    unsupported = [claim for claim in claims if not claim.supported]
    if unsupported:
        notes.append(
            f"{len(unsupported)} claim(s) lost every citation and are marked unsupported."
        )

    return claims, notes
