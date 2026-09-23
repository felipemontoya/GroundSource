"""Keeping a public endpoint from spending more than it was given.

Three limits, because they answer different threats:

- **Per client, per window.** One reader, or one script, cannot use the
  whole budget. Counted in the process cache under a salted hash of the
  client's address, so no address is ever stored, logged or written to the
  database. The cache is per process, which is correct for the single
  instance this runs as; a second instance would need a shared cache.
- **Per day, in calls.** One busy day cannot spend the month.
- **Per month, in dollars.** The ceiling that holds the bill. Spend is
  estimated from the tokens the provider reports for each call, priced at
  CHAT_PRICE_*_PER_MTOK. Crossing the soft limit logs a warning; reaching
  the hard limit stops generation until the next month (UTC).

Day and month are counted in the database so that a restart does not reset
them. When a limit is reached the endpoint does not fail: it answers
retrieval-only, returning the matching passages without generated text, and
says why. Neither limit touches retrieval; reading the document stays free.

Embedding the question is not counted: at text-embedding-3-small prices it
is four orders of magnitude cheaper than the answer.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import F, Sum
from django.http import HttpRequest

from .models import DailyUsage

logger = logging.getLogger(__name__)


def _today():
    return datetime.now(timezone.utc).date()


def client_key(request: HttpRequest) -> str:
    """A salted, truncated hash of the client's address. Never the address.

    Which header carries the real address depends on the proxy in front:
    behind Render it is True-Client-IP, set by its Cloudflare edge, which
    overwrites whatever the client sent. Locally there is no proxy and
    REMOTE_ADDR is the client.
    """
    header = settings.CLIENT_IP_HEADER
    address = ""
    if header:
        address = request.META.get("HTTP_" + header.upper().replace("-", "_"), "")
    address = address.split(",")[0].strip() or request.META.get("REMOTE_ADDR", "")
    digest = hashlib.sha256(f"{settings.SECRET_KEY}:{address}".encode()).hexdigest()
    return digest[:24]


def allow_client(request: HttpRequest) -> bool:
    """Count one question against this client's window; False once it is spent."""
    limit = settings.ASK_PER_CLIENT_LIMIT
    if limit <= 0:
        return True
    window = settings.ASK_PER_CLIENT_WINDOW_SECONDS
    key = f"ask:{client_key(request)}"
    # add() only sets the key if it is absent, so the window starts at the
    # first question and is not extended by later ones.
    cache.add(key, 0, timeout=window)
    try:
        count = cache.incr(key)
    except ValueError:  # expired between add() and incr()
        cache.set(key, 1, timeout=window)
        count = 1
    return count <= limit


def cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * settings.CHAT_PRICE_INPUT_PER_MTOK
        + output_tokens * settings.CHAT_PRICE_OUTPUT_PER_MTOK
    ) / 1_000_000


def month_spend_usd() -> float:
    """Estimated generation spend so far this calendar month (UTC)."""
    today = _today()
    totals = DailyUsage.objects.filter(day__gte=today.replace(day=1)).aggregate(
        input=Sum("input_tokens"), output=Sum("output_tokens")
    )
    return cost_usd(totals["input"] or 0, totals["output"] or 0)


def reserve_model_call() -> str | None:
    """Take one model call from the budget; None if granted, else the reason why not.

    The daily count is taken with a conditional UPDATE rather than
    read-then-write, so that two questions arriving together cannot both
    take the last call. The monthly check reads recorded spend, so it can
    overshoot by the calls in flight when the limit is crossed — cents.
    """
    today = _today()
    DailyUsage.objects.get_or_create(day=today)

    hard = settings.ASK_MONTHLY_HARD_LIMIT_USD
    if hard > 0 and month_spend_usd() >= hard:
        DailyUsage.objects.filter(day=today).update(refused_calls=F("refused_calls") + 1)
        return "The monthly budget for generated answers has been reached; generation resumes next month (UTC)."

    limit = settings.ASK_DAILY_MODEL_LIMIT
    with transaction.atomic():
        rows = DailyUsage.objects.filter(day=today)
        if limit > 0:
            rows = rows.filter(model_calls__lt=limit)
        taken = rows.update(model_calls=F("model_calls") + 1)
        if not taken:
            DailyUsage.objects.filter(day=today).update(refused_calls=F("refused_calls") + 1)
            return "The daily limit on generated answers has been reached; generation resumes tomorrow (UTC)."
    return None


def release_model_call() -> None:
    """Give back a reservation for a call the provider never ran."""
    DailyUsage.objects.filter(day=_today(), model_calls__gt=0).update(
        model_calls=F("model_calls") - 1
    )


def record_tokens(input_tokens: int | None, output_tokens: int | None) -> None:
    """Add a call's reported usage to today's totals, and warn at the soft limit."""
    soft = settings.ASK_MONTHLY_SOFT_LIMIT_USD
    hard = settings.ASK_MONTHLY_HARD_LIMIT_USD
    before = month_spend_usd() if (soft > 0 or hard > 0) else 0.0

    DailyUsage.objects.filter(day=_today()).update(
        input_tokens=F("input_tokens") + (input_tokens or 0),
        output_tokens=F("output_tokens") + (output_tokens or 0),
    )

    if soft > 0 or hard > 0:
        after = before + cost_usd(input_tokens or 0, output_tokens or 0)
        for name, limit in (("soft", soft), ("hard", hard)):
            if limit > 0 and before < limit <= after:
                logger.warning(
                    "Monthly %s limit of USD %.2f crossed: estimated spend this month is USD %.2f.",
                    name, limit, after,
                )
