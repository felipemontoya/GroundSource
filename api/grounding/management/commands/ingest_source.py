"""Ingest one document: bytes in, units out. Costs nothing and needs no key.

Deliberately separate from `embed_source`. Parsing is free, deterministic
and re-runnable; embedding costs money and depends on a provider. Splitting
them means the structural half of the pipeline can be iterated on all day
without spending anything, and it is what lets the stack be useful before
an API key exists.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from grounding import extraction, parsing
from grounding.models import Page, Source, Unit


class Command(BaseCommand):
    help = "Ingest a document into the database: extract, parse, anchor."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to the document, absolute or under SOURCES_DIR.")
        parser.add_argument("--slug", help="Stable handle. Derived from the filename if omitted.")
        parser.add_argument("--title", help="Overrides the title found in the file's metadata.")
        parser.add_argument(
            "--language",
            default="english",
            help="PostgreSQL text search configuration, e.g. english or spanish.",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Re-ingest even if this checksum is already present, replacing its units.",
        )

    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.is_absolute():
            path = settings.SOURCES_DIR / path
        if not path.is_file():
            raise CommandError(f"No such file: {path}")

        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        slug = options["slug"] or slugify(path.stem)[:128]

        existing = Source.objects.filter(slug=slug).first()
        if existing and not options["replace"]:
            if existing.sha256 == digest:
                raise CommandError(
                    f"'{slug}' is already ingested with this exact checksum. "
                    "Pass --replace to re-derive it."
                )
            raise CommandError(
                f"'{slug}' exists with a different checksum ({existing.sha256[:12]}… "
                f"vs {digest[:12]}…). A changed document is a new source, not an edit: "
                "choose a new --slug, or pass --replace if this really is a correction."
            )

        self.stdout.write(f"Reading   {path.name} ({len(data):,} bytes, sha256 {digest[:16]}…)")

        result = extraction.extract(data, path_hint=path.stem)
        self.stdout.write(
            f"Extracted {len(result.text):,} characters from {result.page_count} pages "
            f"using {result.extractor}"
        )

        parsed = parsing.parse_units(result.text)
        self.stdout.write(f"Parsed    {len(parsed)} units")

        with transaction.atomic():
            if existing:
                existing.delete()

            source = Source.objects.create(
                slug=slug,
                title=options["title"] or result.title or path.stem,
                filename=path.name,
                sha256=digest,
                byte_size=len(data),
                page_count=result.page_count,
                canonical_text=result.text,
                language=options["language"],
                extractor=result.extractor,
                pipeline_version=settings.PIPELINE_VERSION,
            )

            Page.objects.bulk_create(
                Page(
                    source=source,
                    number=page.number,
                    start_offset=page.start_offset,
                    end_offset=page.end_offset,
                )
                for page in result.pages
            )

            # Two passes: rows first so that every unit has a primary key,
            # then parents, because a tree cannot be bulk-created in one go
            # without the parent already existing.
            units = [
                Unit(
                    source=source,
                    kind=unit.kind,
                    path=unit.path,
                    heading=unit.heading,
                    ordinal=ordinal,
                    depth=unit.depth,
                    start_offset=unit.start_offset,
                    end_offset=unit.end_offset,
                    page_start=result.page_for(unit.start_offset),
                    page_end=result.page_for(max(unit.start_offset, unit.end_offset - 1)),
                    text=result.text[unit.start_offset : unit.end_offset],
                )
                for ordinal, unit in enumerate(parsed)
            ]
            Unit.objects.bulk_create(units)

            by_ordinal = {unit.ordinal: unit for unit in units}
            reparented = []
            for ordinal, parsed_unit in enumerate(parsed):
                if parsed_unit.parent_index is not None:
                    child = by_ordinal[ordinal]
                    child.parent = by_ordinal[parsed_unit.parent_index]
                    reparented.append(child)
            Unit.objects.bulk_update(reparented, ["parent"])

            self._index_text(source)

        self.stdout.write(
            self.style.SUCCESS(
                f"Ingested '{slug}': {len(units)} units, {result.page_count} pages. "
                f"Next: manage.py verify_anchors {slug}"
            )
        )

    def _index_text(self, source: Source) -> None:
        """Build the full-text index in the source's own language.

        Done in SQL rather than through the ORM because the text search
        configuration is a runtime value — the test bed is English and the
        target document is Spanish — and Django's SearchVector wants it as a
        compile-time argument.
        """
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE grounding_unit
                SET search_vector = setweight(to_tsvector(%s::regconfig, coalesce(heading, '')), 'A')
                                  || setweight(to_tsvector(%s::regconfig, text), 'B')
                WHERE source_id = %s
                """,
                [source.language, source.language, source.pk],
            )
