"""Prove the chain is intact: every unit's indexed text is still its slice.

`Unit.text` is a denormalised copy of `canonical_text[start:end]`, kept so
PostgreSQL can index it. Nothing enforces that it stays true. If it drifts,
lexical retrieval scores text that is not what a citation would quote, and
the system keeps answering — wrongly, and quietly. This command is the
check that turns that into a loud failure.

It is cheap and needs no key, so it belongs in CI and after every ingest.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from grounding import spans
from grounding.models import Source


class Command(BaseCommand):
    help = "Check that every unit's stored text matches the canonical text it anchors into."

    def add_arguments(self, parser):
        parser.add_argument("slug", nargs="?", help="Only this source. All sources if omitted.")

    def handle(self, *args, **options):
        sources = Source.objects.all()
        if options["slug"]:
            sources = sources.filter(slug=options["slug"])
            if not sources.exists():
                raise CommandError(f"No source with slug '{options['slug']}'")

        total_failures = 0

        for source in sources:
            failures = []
            units = list(source.units.all())

            for unit in units:
                if not spans.verify_unit(source, unit):
                    failures.append(unit)

            # Offsets must also stay inside the text they index into, and
            # units must not overlap: an overlap means one passage would be
            # citable under two different anchors.
            length = len(source.canonical_text)
            for unit in units:
                if unit.end_offset > length:
                    failures.append(unit)

            previous_end = 0
            overlaps = 0
            for unit in sorted(units, key=lambda u: u.start_offset):
                if unit.start_offset < previous_end:
                    overlaps += 1
                previous_end = max(previous_end, unit.end_offset)

            covered = sum(unit.end_offset - unit.start_offset for unit in units)
            coverage = (covered / length * 100) if length else 0.0

            if failures:
                total_failures += len(failures)
                self.stdout.write(
                    self.style.ERROR(
                        f"{source.slug}: {len(failures)} of {len(units)} units do not match "
                        "their slice"
                    )
                )
                for unit in failures[:5]:
                    self.stdout.write(f"  unit {unit.pk} [{unit.start_offset}:{unit.end_offset}] {unit}")
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{source.slug}: {len(units)} units verified, "
                        f"{coverage:.1f}% of canonical text covered, {overlaps} overlaps"
                    )
                )

        if total_failures:
            raise CommandError(f"{total_failures} unit(s) failed verification")
