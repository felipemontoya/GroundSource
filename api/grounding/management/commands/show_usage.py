"""Print recent daily usage: what the cap allowed, refused, and consumed.

The token totals are what the daily cap should be calibrated against: the
provider's per-token price times these numbers is the day's bill.
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand

from grounding.models import DailyUsage


class Command(BaseCommand):
    help = "Show model calls, refusals and tokens per day."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14)

    def handle(self, *args, **options):
        limit = settings.ASK_DAILY_MODEL_LIMIT or "none"
        self.stdout.write(f"Daily model-call limit: {limit}  ({settings.CHAT_MODEL})")
        self.stdout.write(f"{'day':<12}{'calls':>7}{'refused':>9}{'input tok':>12}{'output tok':>12}")
        for row in DailyUsage.objects.all()[: options["days"]]:
            self.stdout.write(
                f"{row.day.isoformat():<12}{row.model_calls:>7}{row.refused_calls:>9}"
                f"{row.input_tokens:>12,}{row.output_tokens:>12,}"
            )
