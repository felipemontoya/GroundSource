"""Canonical text → a tree of units, with offsets carried through.

Structure-first, not size-first. The document's own numbering decides where
a unit begins and ends, because that is what a citation has to name: a
reader checks "1.4 Policy", not "chunk 37". Fixed-size chunking would cut
across the boundaries the whole product is built to point at.

Everything here is deterministic and offset-preserving: a unit's text is
never rebuilt from pieces, only delimited by a start and an end into the
canonical text it came from.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

PARSER_VERSION = "units/1"

# "1." / "1.2" / "3.4.1", optionally followed by a trailing dot, then a
# title. Requiring the title to start with a letter in upper case is what
# keeps "2016. The company moved..." in a body paragraph out of the tree.
_HEADING = re.compile(
    r"^(?P<number>\d+(?:\.\d+)*)\.?[ \t ]*(?P<title>[A-ZÁÉÍÓÚÑ][^\n]*?)[ \t]*$"
)

# A line holding nothing but a page number, which every exported document
# has and no reader ever quotes.
_PAGE_NUMBER = re.compile(r"^\s*\d{1,4}\s*$")

_TOC_MARKER = re.compile(r"^\s*(TABLE OF CONTENTS|CONTENTS|ÍNDICE|TABLA DE CONTENIDO)\s*$", re.I)

# Headings are short. A numbered line that runs long is a numbered sentence.
_MAX_HEADING_CHARS = 120


@dataclass
class ParsedUnit:
    kind: str
    start_offset: int
    end_offset: int
    path: str = ""
    heading: str = ""
    depth: int = 0
    parent_index: int | None = None
    children: list[int] = field(default_factory=list)


@dataclass
class _Line:
    start: int
    end: int
    text: str


def _lines(text: str) -> list[_Line]:
    """Every line with its exact range in `text`, newlines excluded."""
    out: list[_Line] = []
    position = 0
    for raw in text.split("\n"):
        out.append(_Line(start=position, end=position + len(raw), text=raw))
        position += len(raw) + 1
    return out


def _toc_region(lines: list[_Line]) -> tuple[int, int] | None:
    """Line indices covering a table of contents, if there is one.

    A TOC is numbered exactly like the body it lists, so leaving it in
    produces a duplicate tree whose offsets point at the index instead of at
    the text. It ends at the first blank run following a page-number line —
    which is where the exported page break falls.
    """
    for index, line in enumerate(lines):
        if _TOC_MARKER.match(line.text):
            for end in range(index + 1, len(lines)):
                if _PAGE_NUMBER.match(lines[end].text) and lines[end].text.strip():
                    return index, end
            return index, len(lines) - 1
    return None


def _is_heading(line: _Line) -> re.Match | None:
    if len(line.text) > _MAX_HEADING_CHARS:
        return None
    return _HEADING.match(line.text)


def parse_units(text: str) -> list[ParsedUnit]:
    """Delimit the document's units. Returns them in document order."""
    lines = _lines(text)
    toc = _toc_region(lines)
    toc_range = range(toc[0], toc[1] + 1) if toc else range(0, 0)

    units: list[ParsedUnit] = []
    # path prefix -> index of the unit that owns it, for parent resolution
    open_headings: dict[int, int] = {}

    body_start: int | None = None
    body_end: int | None = None
    current_parent: int | None = None

    def flush_body() -> None:
        """Close the run of body lines accumulated so far into paragraphs."""
        nonlocal body_start, body_end
        if body_start is None or body_end is None:
            return
        block = text[body_start:body_end]
        if block.strip():
            for start, end in _paragraphs(block, body_start):
                units.append(
                    ParsedUnit(
                        kind="front_matter" if current_parent is None else "paragraph",
                        start_offset=start,
                        end_offset=end,
                        parent_index=current_parent,
                        depth=(units[current_parent].depth + 1) if current_parent is not None else 0,
                    )
                )
        body_start = body_end = None

    for index, line in enumerate(lines):
        # Blank lines, page numbers and the table of contents end a body run
        # but are never units themselves. They stay in the canonical text —
        # skipping them as *structure* is not the same as removing them, and
        # removing them would move every offset after this point.
        if not line.text.strip() or index in toc_range or _PAGE_NUMBER.match(line.text):
            flush_body()
            continue

        match = _is_heading(line)
        if match:
            flush_body()
            path = match.group("number")
            depth = path.count(".")
            unit_index = len(units)
            units.append(
                ParsedUnit(
                    kind="heading",
                    start_offset=line.start,
                    end_offset=line.end,
                    path=path,
                    heading=match.group("title").strip(),
                    depth=depth,
                    parent_index=open_headings.get(depth - 1) if depth > 0 else None,
                )
            )
            open_headings[depth] = unit_index
            for deeper in [d for d in open_headings if d > depth]:
                del open_headings[deeper]
            current_parent = unit_index
            continue

        if body_start is None:
            body_start = line.start
        body_end = line.end

    flush_body()

    for position, unit in enumerate(units):
        if unit.parent_index is not None:
            units[unit.parent_index].children.append(position)

    return units


def _paragraphs(block: str, base_offset: int) -> list[tuple[int, int]]:
    """Split a run of body text into paragraphs, as (start, end) in the source.

    Offsets are computed from the block's own position, never by searching
    for the text again — searching is how a duplicate line silently anchors
    to the wrong place.
    """
    spans: list[tuple[int, int]] = []
    start: int | None = None
    position = 0
    for raw in block.split("\n"):
        if raw.strip():
            if start is None:
                start = position
            end = position + len(raw)
        elif start is not None:
            spans.append((base_offset + start, base_offset + end))
            start = None
        position += len(raw) + 1
    if start is not None:
        spans.append((base_offset + start, base_offset + end))
    return spans
