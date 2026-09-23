"""The provider seam.

Every call that leaves this machine goes through here. That is the point:
the provider is an open decision (../AGENTS.md), and keeping it to one file
means changing it is an edit rather than an excavation.

It also enforces the division of labour the hardware forces. There is no GPU
here, so nothing heavy runs locally — embeddings and generation are remote
calls, and the local containers stay small enough to rebuild in seconds.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)


class ProviderUnavailable(RuntimeError):
    """No usable credentials, or the provider refused. Reported, not swallowed."""


@dataclass(frozen=True)
class Completion:
    payload: dict
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


def is_configured() -> bool:
    return bool(settings.OPENAI_API_KEY)


def _client():
    if not is_configured():
        raise ProviderUnavailable(
            "OPENAI_API_KEY is not set. Ingestion and lexical retrieval work "
            "without it; embeddings and answering do not."
        )
    from openai import OpenAI

    return OpenAI(api_key=settings.OPENAI_API_KEY)


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a batch, returning vectors in the order given.

    Batched because the per-request overhead dominates at this document's
    size, and order-checked because a silently reordered batch would attach
    every vector to the wrong unit — a failure that looks like poor
    retrieval rather than like a bug.
    """
    if not texts:
        return []

    response = _client().embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts,
    )
    items = sorted(response.data, key=lambda item: item.index)
    if len(items) != len(texts):
        raise ProviderUnavailable(f"asked for {len(texts)} embeddings, received {len(items)}")

    vectors = [item.embedding for item in items]
    width = len(vectors[0])
    if width != settings.EMBEDDING_DIMENSIONS:
        raise ProviderUnavailable(
            f"{settings.EMBEDDING_MODEL} returned {width}-dimensional vectors, "
            f"but the schema stores {settings.EMBEDDING_DIMENSIONS}. "
            "Changing embedding model is a migration, not a setting."
        )
    return vectors


def complete_json(*, instructions: str, prompt: str, schema: dict) -> Completion:
    """Ask for one structured answer.

    Structured output is not a convenience here. The answering contract is
    that the model selects anchors and never writes quotations, and a schema
    that has slots for unit ids and offset ranges — and no slot for quoted
    text — is what makes that mechanical instead of aspirational.
    """
    client = _client()
    model = settings.CHAT_MODEL

    try:
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=prompt,
            max_output_tokens=settings.CHAT_MAX_OUTPUT_TOKENS,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "grounded_answer",
                    "schema": schema,
                    "strict": True,
                }
            },
        )
    except Exception as exc:  # provider, network, or an unknown model name
        raise ProviderUnavailable(f"{type(exc).__name__}: {exc}") from exc

    text = getattr(response, "output_text", "") or ""
    if not text.strip():
        raise ProviderUnavailable(f"{model} returned an empty response")

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderUnavailable(f"{model} returned text that is not JSON: {exc}") from exc

    usage = getattr(response, "usage", None)
    return Completion(
        payload=payload,
        model=model,
        input_tokens=getattr(usage, "input_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None),
    )
