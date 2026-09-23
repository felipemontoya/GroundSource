"""The HTTP surface: what a page can ask for.

Three endpoints, all JSON, all read-only. There is no conversation state
yet — a question is answered from the document, not from what was asked
before it — because conversation history is Phase 1 and adding it now would
mean deciding how prior turns affect retrieval before anything retrieves
well.
"""

from __future__ import annotations

import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import answering, limits, llm
from .models import Source

MAX_QUESTION_CHARS = 1000


@require_GET
def sources(request: HttpRequest) -> JsonResponse:
    """What documents are loaded, and whether they are ready to be asked about."""
    payload = []
    for source in Source.objects.all():
        embedded = (
            Source.objects.filter(pk=source.pk)
            .values_list("units__embeddings__id", flat=True)
            .exclude(units__embeddings__id=None)
            .count()
        )
        payload.append(
            {
                "slug": source.slug,
                "title": source.title,
                "edition": source.edition,
                "nickname": source.nickname,
                "filename": source.filename,
                "sha256": source.sha256,
                "pages": source.page_count,
                "characters": len(source.canonical_text),
                "units": source.units.count(),
                "embedded_units": embedded,
                "language": source.language,
                "extractor": source.extractor,
                "pipeline_version": source.pipeline_version,
                "ingested_at": source.ingested_at.isoformat(),
            }
        )
    return JsonResponse(
        {
            "sources": payload,
            "provider_configured": llm.is_configured(),
        },
        json_dumps_params={"indent": 2},
    )


@require_GET
def outline(request: HttpRequest, slug: str) -> JsonResponse:
    """The document's own structure, so a reader can see what there is to ask about."""
    try:
        source = Source.objects.get(slug=slug)
    except Source.DoesNotExist:
        return JsonResponse({"error": f"No source '{slug}'"}, status=404)

    headings = source.units.filter(kind="heading").order_by("ordinal")
    return JsonResponse(
        {
            "slug": source.slug,
            "title": source.title,
            "edition": source.edition,
            "nickname": source.nickname,
            "headings": [
                {
                    "unit_id": unit.pk,
                    "path": unit.path,
                    "heading": unit.heading,
                    "depth": unit.depth,
                    "page": unit.page_start,
                }
                for unit in headings
            ],
        },
        json_dumps_params={"indent": 2},
    )


@csrf_exempt
@require_POST
def ask(request: HttpRequest, slug: str) -> JsonResponse:
    """Answer one question about one document, or decline to.

    CSRF-exempt because the page is a separate static origin with no session
    and nothing to forge: the endpoint reads, never writes, and carries no
    credentials. That stops being true the moment conversations are stored,
    which is the point at which this decorator has to go.
    """
    try:
        source = Source.objects.get(slug=slug)
    except Source.DoesNotExist:
        return JsonResponse({"error": f"No source '{slug}'"}, status=404)

    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Body must be JSON"}, status=400)

    question = str(body.get("question", "")).strip()
    if not question:
        return JsonResponse({"error": "A 'question' is required"}, status=400)
    if len(question) > MAX_QUESTION_CHARS:
        return JsonResponse(
            {"error": f"Question is longer than {MAX_QUESTION_CHARS} characters"}, status=400
        )

    if not limits.allow_client(request):
        return JsonResponse(
            {"error": "Too many questions from this client. Try again later."}, status=429
        )

    answer = answering.answer_question(source, question)
    return JsonResponse(answer.as_dict(), json_dumps_params={"indent": 2})
