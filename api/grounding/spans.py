"""Where quotations come from.

Invariant 4 of ../AGENTS.md: quoted spans are sliced from the source
programmatically, never produced by a model. Model output may select
anchors; it may not author quotations.

This module is the only place a quotation is produced, so that the rule has
one enforcement point rather than a convention repeated at every call site.
A model hands in an offset range; `quote()` decides whether that range is
real and returns the document's own characters or nothing at all.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Source, Unit

# A quotation shorter than this is not evidence, it is a fragment.
MIN_QUOTE_CHARS = 12


class SpanError(ValueError):
    """A requested span does not resolve. Never recoverable by adjusting it."""


@dataclass(frozen=True)
class Quote:
    """A verbatim run of source text, and the anchor that locates it."""

    unit_id: int
    path: str
    page_start: int | None
    page_end: int | None
    start_offset: int
    end_offset: int
    text: str

    def as_dict(self) -> dict:
        return {
            "unit_id": self.unit_id,
            "path": self.path,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "text": self.text,
        }


def quote_unit(source: Source, unit: Unit) -> Quote:
    """The whole unit, sliced from canonical text."""
    return _build(source, unit, unit.start_offset, unit.end_offset)


def quote_within(source: Source, unit: Unit, start: int, end: int) -> Quote:
    """A range *inside* a unit, given in characters from the unit's start.

    Relative offsets are what a model is asked for, because absolute ones
    invite it to invent a plausible-looking number that lands somewhere else
    in the document. A relative range that overflows its unit is rejected
    here rather than clamped: a clamp would return real text that answers a
    different question, which is worse than returning nothing.
    """
    if start < 0 or end <= start:
        raise SpanError(f"span [{start}:{end}] is not a forward range")

    length = unit.end_offset - unit.start_offset
    if end > length:
        raise SpanError(f"span [{start}:{end}] overflows unit {unit.pk} of length {length}")

    return _build(source, unit, unit.start_offset + start, unit.start_offset + end)


def _build(source: Source, unit: Unit, start: int, end: int) -> Quote:
    text = source.slice(start, end)
    if not text.strip():
        raise SpanError(f"span [{start}:{end}] of unit {unit.pk} is empty")
    return Quote(
        unit_id=unit.pk,
        path=unit.path,
        page_start=unit.page_start,
        page_end=unit.page_end,
        start_offset=start,
        end_offset=end,
        text=text,
    )


def verify_unit(source: Source, unit: Unit) -> bool:
    """Does the unit's indexed copy still match the slice it claims to be?

    `Unit.text` exists only so PostgreSQL can index it. If it ever diverges
    from `canonical_text[start:end]`, lexical retrieval is scoring text that
    is not what a citation would quote, and the chain is broken without
    anything failing. `manage.py verify_anchors` calls this over everything.
    """
    return source.slice(unit.start_offset, unit.end_offset) == unit.text
