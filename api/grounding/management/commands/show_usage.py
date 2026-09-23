"""Print recent daily usage: what the limits allowed, refused, and consumed.

Cost is estimated from the tokens the provider reported, priced at
CHAT_PRICE_*_PER_MTOK — the same estimate the monthly limits are enforced
against. The provider's own dashboard is the authority on the real bill.
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand

from grounding import limits
from grounding.models import DailyUsage


class Command(BaseCommand):
    help = "Show model calls, refusals, tokens and estimated cost per day, and this month's spend."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14)

    def handle(self, *args, **options):
        def show(value):
            return value or "none"

        self.stdout.write(
            f"{settings.CHAT_MODEL} at USD {settings.CHAT_PRICE_INPUT_PER_MTOK} / "
            f"{settings.CHAT_PRICE_OUTPUT_PER_MTOK} per million tokens"
        )
        self.stdout.write(
            f"Limits: {show(settings.ASK_DAILY_MODEL_LIMIT)} calls/day, monthly soft "
            f"USD {show(settings.ASK_MONTHLY_SOFT_LIMIT_USD)}, hard USD "
            f"{show(settings.ASK_MONTHLY_HARD_LIMIT_USD)}"
        )
        self.stdout.write(f"This month so far: USD {limits.month_spend_usd():.4f}")
        self.stdout.write("")
        self.stdout.write(
            f"{'day':<12}{'calls':>7}{'refused':>9}{'input tok':>12}{'output tok':>12}{'USD':>10}"
        )
        for row in DailyUsage.objects.all()[: options["days"]]:
            cost = limits.cost_usd(row.input_tokens, row.output_tokens)
            self.stdout.write(
                f"{row.day.isoformat():<12}{row.model_calls:>7}{row.refused_calls:>9}"
                f"{row.input_tokens:>12,}{row.output_tokens:>12,}{cost:>10.4f}"
            )
