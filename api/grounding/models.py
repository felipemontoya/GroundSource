"""The chain, as tables.

    original bytes → character offsets → structural anchor → quoted span

`Source` holds the first link and `Unit` the middle two. The last link is
deliberately *not* a column: a quoted span is produced by slicing
`Source.canonical_text`, never by reading something a model wrote. See
`spans.py`.

One Django app holds all of this for now. That does not settle the open
decision in ../AGENTS.md about how pipeline stages map onto apps; it is the
smallest thing that lets a proof of concept exist, and splitting it later is
a migration, not a rewrite.
"""

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from pgvector.django import HnswIndex, VectorField

# Every embedding in this table lives in one vector space. The dimension is
# fixed in the schema because mixing dimensions in a column is not a thing
# pgvector allows, and a second embedding model with a different width is a
# migration, not a configuration change.
EMBEDDING_DIMENSIONS = 1536


class Source(models.Model):
    """An ingested document: the immutable original, plus what was derived.

    The bytes themselves stay on disk in `sources/`. What lives here is the
    checksum that identifies them and the canonical text that offsets are
    measured against.
    """

    slug = models.SlugField(max_length=128, unique=True)
    title = models.TextField()

    # Which edition this is, in words a reader recognises: "JEP, 2018
    # typesetting", "Cancillería, 24 Nov 2016". Two typesettings of the same
    # agreement are two sources, not one source and one substitute — they
    # paginate differently, and a citation names a page in *this* file. The
    # title usually comes from PDF metadata and is not reliably distinct, so
    # this is set by hand at ingest.
    edition = models.CharField(max_length=200, blank=True, default="")

    # How the page refers to the document in running text: "el acuerdo",
    # "la ley", "el decreto", "el RFP". A rendering label only: it is not
    # sent to the model and not added to any retrieval query. Set by hand.
    nickname = models.CharField(max_length=100, blank=True, default="")

    # --- the immutable original ------------------------------------------
    filename = models.TextField(help_text="Name of the file as ingested.")
    sha256 = models.CharField(max_length=64, db_index=True)
    byte_size = models.BigIntegerField()
    media_type = models.CharField(max_length=128, default="application/pdf")
    page_count = models.IntegerField(null=True, blank=True)

    # --- the canonical text offsets refer to ------------------------------
    # Derived, regenerable, and the coordinate system for every anchor. It is
    # stored rather than recomputed so that a span can be sliced without
    # reopening the original, and so that a changed extractor shows up as a
    # changed row instead of silently moving every offset.
    canonical_text = models.TextField()

    # PostgreSQL text search configuration for this source's language, e.g.
    # 'english' or 'spanish'. Held per source because the target document is
    # Spanish while the current test bed is English.
    language = models.CharField(max_length=32, default="english")

    # --- provenance of the derivation -------------------------------------
    extractor = models.CharField(
        max_length=128,
        help_text="Library and version that produced canonical_text, e.g. 'pdfplumber/0.11.10'.",
    )
    pipeline_version = models.CharField(max_length=32)
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["slug"]

    def __str__(self) -> str:
        return self.slug

    def slice(self, start: int, end: int) -> str:
        """The only sanctioned way to obtain text that claims to be verbatim."""
        return self.canonical_text[start:end]


class Page(models.Model):
    """Where a character range falls in the original's pagination.

    This is what makes a citation resolvable by a human holding the PDF: an
    offset points into a derived string, a page number points into the
    document they can open.
    """

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="pages")
    number = models.IntegerField()
    start_offset = models.IntegerField()
    end_offset = models.IntegerField()

    class Meta:
        ordering = ["source", "number"]
        constraints = [
            models.UniqueConstraint(fields=["source", "number"], name="unique_page_per_source"),
        ]

    def __str__(self) -> str:
        return f"{self.source.slug} p.{self.number}"


class Unit(models.Model):
    """An addressable structural node.

    `path` plus (`start_offset`, `end_offset`) is the anchor. ../AGENTS.md
    makes anchors part of the public API, so nothing may regenerate them in a
    way that moves them without the pipeline version changing too.
    """

    class Kind(models.TextChoices):
        HEADING = "heading"
        PARAGRAPH = "paragraph"
        LIST_ITEM = "list_item"
        TABLE = "table"
        FRONT_MATTER = "front_matter"

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="units")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )

    kind = models.CharField(max_length=16, choices=Kind.choices)

    # Dotted path through the document's own numbering, e.g. "1.2". Empty for
    # nodes the document does not number. Borrowed in spirit from Akoma
    # Ntoso's identifier discipline (docs/planning/prior-art.md §4.1) without
    # adopting the serialisation.
    path = models.CharField(max_length=128, blank=True, db_index=True)
    heading = models.TextField(blank=True, help_text="The unit's own title, if it has one.")

    # Document order. The tie-breaker for presentation, so that retrieval
    # relevance never decides what a reader sees first within a section.
    ordinal = models.IntegerField()
    depth = models.IntegerField(default=0)

    # --- the anchor -------------------------------------------------------
    start_offset = models.IntegerField()
    end_offset = models.IntegerField()
    page_start = models.IntegerField(null=True, blank=True)
    page_end = models.IntegerField(null=True, blank=True)

    # A denormalised copy of source.canonical_text[start_offset:end_offset],
    # kept only so PostgreSQL can index it for lexical search. It is never
    # the thing quoted back to a reader, and `manage.py verify_anchors`
    # exists to prove it has not drifted from the slice it mirrors.
    text = models.TextField()
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        ordering = ["source", "ordinal"]
        constraints = [
            models.UniqueConstraint(fields=["source", "ordinal"], name="unique_ordinal_per_source"),
            models.CheckConstraint(
                condition=models.Q(end_offset__gt=models.F("start_offset")),
                name="unit_range_is_non_empty",
            ),
        ]
        indexes = [
            models.Index(fields=["source", "path"]),
            GinIndex(fields=["search_vector"], name="unit_search_vector_gin"),
        ]

    def __str__(self) -> str:
        return f"{self.source.slug}#{self.path or self.ordinal}"

    @property
    def anchor(self) -> dict:
        return {
            "unit_id": self.pk,
            "path": self.path,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "page_start": self.page_start,
            "page_end": self.page_end,
        }


class Embedding(models.Model):
    """One unit's vector, under one model.

    Separate from `Unit` so that re-embedding under a different model adds
    rows instead of destroying the unit, and so that every vector carries the
    model that produced it — invariant 3, derived data records what made it.
    """

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="embeddings")
    vector = VectorField(dimensions=EMBEDDING_DIMENSIONS)
    model = models.CharField(max_length=128)
    pipeline_version = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["unit", "model"], name="one_vector_per_unit_per_model"),
        ]
        indexes = [
            # Cosine distance, to match how the embeddings are normalised by
            # the provider. An HNSW index is overkill at this size and is
            # here so that the query plan does not change shape later.
            HnswIndex(
                name="embedding_vector_hnsw",
                fields=["vector"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.unit} [{self.model}]"
