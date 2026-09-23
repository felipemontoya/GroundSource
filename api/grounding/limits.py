"""Keeping a public endpoint from spending more than it was given.

Two independent limits, because they answer different threats:

- **Per client, per window.** One reader, or one script, cannot use the
  whole day's budget. Counted in the process cache under a salted hash of
  the client's address, so no address is ever stored, logged or written to
  the database. The cache is per process, which is correct for the single
  instance this runs as; a second instance would need a shared cache.
- **Per day, globally.** The ceiling on model calls, and the one that holds
  the bill. Counted in the database so that a restart does not reset it.
  When it is reached the endpoint does not fail: it answers retrieval-only,
  returning the matching passages without generated text, and says why.

Neither limit touches retrieval. Reading the document stays free.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.http import HttpRequest

from .models import DailyUsage


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


def reserve_model_call() -> bool:
    """Take one model call from today's budget, atomically; False when none is left.

    A conditional UPDATE rather than read-then-write, so that two questions
    arriving together cannot both take the last call.
    """
    limit = settings.ASK_DAILY_MODEL_LIMIT
    today = _today()
    DailyUsage.objects.get_or_create(day=today)
    if limit <= 0:
        DailyUsage.objects.filter(day=today).update(model_calls=F("model_calls") + 1)
        return True
    with transaction.atomic():
        taken = DailyUsage.objects.filter(day=today, model_calls__lt=limit).update(
            model_calls=F("model_calls") + 1
        )
        if not taken:
            DailyUsage.objects.filter(day=today).update(refused_calls=F("refused_calls") + 1)
    return bool(taken)


def record_tokens(input_tokens: int | None, output_tokens: int | None) -> None:
    """Add a call's reported usage to today's totals, for calibrating the cap."""
    DailyUsage.objects.filter(day=_today()).update(
        input_tokens=F("input_tokens") + (input_tokens or 0),
        output_tokens=F("output_tokens") + (output_tokens or 0),
    )
