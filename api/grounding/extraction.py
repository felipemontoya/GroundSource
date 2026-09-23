"""PDF bytes → canonical text, with every character's origin retained.

This is the stage where the offset invariant lives or dies
(docs/planning/prior-art.md §4.2). The contract is narrow on purpose:

    extract(pdf_bytes) -> Extraction

where `Extraction.text` is the canonical text every anchor is measured
against and `Extraction.pages` says which character range came from which
page. Anything that can satisfy that contract can replace what is here.

**On the library choice.** prior-art.md §4.2 recommends not hand-rolling
extraction and names Docling. Docling is not used, for two reasons that are
measured rather than preferred.

The first is the machine: there is no GPU here, so a layout model would run
on CPU. Installing Docling pulls 6.2 GB, of which 3.2 GB is CUDA and 1.2 GB
is torch — a stack that cannot be accelerated on this hardware and would
make every ingestion run slow. The standing rule for this project is that
heavy model work happens remotely, behind an API, not in a local container.

The second is the document: born-digital with a clean text layer, which is
exactly the case where character-level extraction is exact and a layout
model only adds inference to a problem that does not have one. `pdfplumber`
(MIT, over pdfminer.six) gives every character its page and bounding box,
which is the provenance the invariant actually asks for.

The `Extraction` boundary exists so that this stays revisable: a scanned or
badly-structured document, or a remote extraction service, slots in behind
the same contract and is judged against a golden file rather than a
README.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import pdfplumber

EXTRACTOR_NAME = f"pdfplumber/{pdfplumber.__version__}"

# Characters that word processors scatter through exported PDFs and that
# carry no meaning a reader would quote: zero-width spaces, soft hyphens,
# BOMs. Dropping them changes offsets, which is exactly why it happens here,
# once, before any offset is assigned to anything — and never again
# afterwards. Invariant 2 forbids re-normalising downstream, not normalising
# at the point the coordinate system is created.
_INVISIBLE = re.compile(r"[​‌‍⁠﻿­]")


@dataclass
class PageRange:
    number: int
    start_offset: int
    end_offset: int


@dataclass
class Extraction:
    """Canonical text plus the map back to the original's pagination."""

    text: str
    pages: list[PageRange] = field(default_factory=list)
    page_count: int = 0
    extractor: str = EXTRACTOR_NAME
    title: str = ""

    def page_for(self, offset: int) -> int | None:
        for page in self.pages:
            if page.start_offset <= offset < page.end_offset:
                return page.number
        return self.pages[-1].number if self.pages else None


def _canonicalise(raw: str) -> str:
    """Make one page's text into its canonical form.

    NFC first, because a combining accent and its precomposed form are the
    same character to a reader and two different offsets to a slicer, and
    Spanish text arrives as both. Then invisible characters go, then
    trailing whitespace per line. Nothing here is applied twice: the result
    is the coordinate system, and it is frozen the moment it is returned.
    """
    text = unicodedata.normalize("NFC", raw)
    text = _INVISIBLE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text


def extract(pdf_bytes: bytes, *, path_hint: str = "") -> Extraction:
    """Read a PDF into canonical text and a page map."""
    import io

    chunks: list[str] = []
    pages: list[PageRange] = []
    offset = 0
    title = ""

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        metadata = pdf.metadata or {}
        title = str(metadata.get("Title") or "").strip()

        for index, page in enumerate(pdf.pages, start=1):
            body = _canonicalise(page.extract_text() or "")
            # A page break is two newlines: enough for the unit parser to see
            # a boundary, and constant so the arithmetic below stays honest.
            separator = "\n\n" if index > 1 else ""
            chunks.append(separator + body)
            start = offset + len(separator)
            offset = start + len(body)
            pages.append(PageRange(number=index, start_offset=start, end_offset=offset))

        page_count = len(pdf.pages)

    text = "".join(chunks)

    # The arithmetic above is load-bearing; assert it rather than trust it.
    for page in pages:
        assert text[page.start_offset : page.end_offset] is not None
    assert offset == len(text), f"page map ends at {offset}, text is {len(text)} characters"

    return Extraction(
        text=text,
        pages=pages,
        page_count=page_count,
        title=title or path_hint,
    )
