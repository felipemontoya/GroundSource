"""Change how an ingested source is named, without re-ingesting it.

Title, edition and nickname are labels a person sets, not text derived from
the file. Changing one touches no offset, anchor or embedding, so it should
not cost a re-ingest — and `ingest_source --replace` would throw the
embeddings away with the units.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from grounding.models import Source

LABELS = ("title", "edition", "nickname")


class Command(BaseCommand):
    help = "Set a source's title, edition or nickname."

    def add_arguments(self, parser):
        parser.add_argument("slug")
        parser.add_argument("--title")
        parser.add_argument("--edition", help="Which typesetting this is: 'JEP, 2018'.")
        parser.add_argument(
            "--nickname",
            help="How the page refers to it: 'el acuerdo', 'la ley'. Empty clears it.",
        )

    def handle(self, *args, **options):
        try:
            source = Source.objects.get(slug=options["slug"])
        except Source.DoesNotExist:
            raise CommandError(f"No source '{options['slug']}'")

        changed = [label for label in LABELS if options[label] is not None]
        if not changed:
            for label in LABELS:
                self.stdout.write(f"{label:9} {getattr(source, label)!r}")
            return

        for label in changed:
            setattr(source, label, options[label].strip())
        source.save(update_fields=changed)

        for label in changed:
            self.stdout.write(f"{label:9} {getattr(source, label)!r}")
        self.stdout.write(self.style.SUCCESS(f"Relabelled '{source.slug}'."))
