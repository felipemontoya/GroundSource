"""Embed a source's units. Costs money, so it is its own command.

Every vector records the model that made it and the pipeline version it was
made under, because invariant 3 asks derived data to be identifiable rather
than merely regenerable. Re-running with a different EMBEDDING_MODEL adds a
second set of vectors instead of overwriting the first.
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from grounding import llm
from grounding.models import Embedding, Source

BATCH = 64


class Command(BaseCommand):
    help = "Compute and store embeddings for a source's units."

    def add_arguments(self, parser):
        parser.add_argument("slug")
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Re-embed units that already have a vector under this model.",
        )

    def handle(self, *args, **options):
        if not llm.is_configured():
            raise CommandError(
                "OPENAI_API_KEY is not set. Put it in dev/.env and restart the api service."
            )

        try:
            source = Source.objects.get(slug=options["slug"])
        except Source.DoesNotExist:
            raise CommandError(f"No source with slug '{options['slug']}'") from None

        model = settings.EMBEDDING_MODEL
        units = list(source.units.order_by("ordinal"))

        if options["replace"]:
            deleted, _ = Embedding.objects.filter(unit__source=source, model=model).delete()
            if deleted:
                self.stdout.write(f"Removed {deleted} existing vector(s) for {model}")
        else:
            already = set(
                Embedding.objects.filter(unit__source=source, model=model).values_list(
                    "unit_id", flat=True
                )
            )
            units = [unit for unit in units if unit.pk not in already]
            if already:
                self.stdout.write(f"Skipping {len(already)} unit(s) already embedded under {model}")

        if not units:
            self.stdout.write(self.style.SUCCESS("Nothing to embed."))
            return

        self.stdout.write(f"Embedding {len(units)} unit(s) with {model} in batches of {BATCH}")
        stored = 0

        for start in range(0, len(units), BATCH):
            batch = units[start : start + BATCH]
            # The heading gives a bare paragraph the context that makes its
            # embedding mean something; without it, "This policy applies to
            # any established business unit" is near-identical to a dozen
            # other clauses.
            texts = [
                f"{unit.heading}\n{unit.text}".strip() if unit.heading else unit.text
                for unit in batch
            ]
            vectors = llm.embed(texts)

            with transaction.atomic():
                Embedding.objects.bulk_create(
                    Embedding(
                        unit=unit,
                        vector=vector,
                        model=model,
                        pipeline_version=settings.PIPELINE_VERSION,
                    )
                    for unit, vector in zip(batch, vectors, strict=True)
                )
            stored += len(batch)
            self.stdout.write(f"  {stored}/{len(units)}")

        self.stdout.write(self.style.SUCCESS(f"Stored {stored} vector(s) under {model}."))
