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

    The range is then snapped outwards to whole words and, where one is
    close by, to whole sentences. Models count characters badly — in
    practice they land a few characters off and produce quotations like
    "imes of crisis" or "…expected to pro". Snapping fixes that in code,
    which is where it belongs: the model still chooses *where* to point, and
    still never supplies a single character of what is quoted.
    """
    if start < 0 or end <= start:
        raise SpanError(f"span [{start}:{end}] is not a forward range")

    length = unit.end_offset - unit.start_offset
    if end > length:
        raise SpanError(f"span [{start}:{end}] overflows unit {unit.pk} of length {length}")

    body = source.slice(unit.start_offset, unit.end_offset)
    start, end = snap(body, start, end)

    return _build(source, unit, unit.start_offset + start, unit.start_offset + end)


# How far snapping will reach to find a sentence boundary before settling
# for a word boundary. Beyond this, growing the quotation costs the reader
# more than the ragged edge did.
SENTENCE_REACH = 180

# Newlines are deliberately absent. Inside a unit they are where the PDF
# wrapped a line, not where the document ended a thought — paragraphs are
# separate units already. Treating them as boundaries ended quotations
# mid-sentence, which is the thing this function exists to prevent.
_SENTENCE_END = (".", "!", "?", "…")


def _sentence_end_after(text: str, index: int) -> int | None:
    """Offset just past the first sentence terminator at or after `index`."""
    for position in range(index, len(text)):
        if text[position] in _SENTENCE_END:
            return position + 1
    return None


def snap(text: str, start: int, end: int) -> tuple[int, int]:
    """Widen [start:end] to whole words, and to whole sentences when near.

    Only ever widens. A range that shrinks could drop the negation, the
    exception, or the subject that changes what the passage means, so the
    failure mode here is quoting slightly too much.
    """
    start = max(0, min(start, len(text)))
    end = max(start, min(end, len(text)))

    # Back up to the start of the sentence this offset sits in, if it is
    # within reach; otherwise just to the start of the current word.
    floor = max(0, start - SENTENCE_REACH)
    sentence_start = None
    for index in range(start - 1, floor - 1, -1):
        if text[index] in _SENTENCE_END:
            sentence_start = index + 1
            break
    if sentence_start is not None:
        # If the requested range only clipped the last character or two of
        # that sentence, it was not aiming at it. Backing up would prepend a
        # whole sentence the reader was never pointed at, so step over it.
        tail = _sentence_end_after(text, sentence_start)
        if tail is not None and tail - start <= 3 and tail < end:
            start = tail
        else:
            start = sentence_start
    else:
        while start > 0 and not text[start - 1].isspace():
            start -= 1
    while start < len(text) and text[start].isspace():
        start += 1

    # Forward to the end of the sentence, or failing that the end of the word.
    ceiling = min(len(text), end + SENTENCE_REACH)
    sentence_end = None
    for index in range(end, ceiling):
        if text[index] in _SENTENCE_END:
            sentence_end = index + 1
            break
    if sentence_end is not None:
        end = sentence_end
    else:
        while end < len(text) and not text[end].isspace():
            end += 1
    while end > start and text[end - 1].isspace():
        end -= 1

    return start, max(end, start + 1)


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
