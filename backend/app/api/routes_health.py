"""Health, readiness and provider configuration."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Response

from app.api.deps import ApplicationContext, get_context
from app.schemas.chunks import DocumentRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["operations"])


@router.get("/health")
def health(context: ApplicationContext = Depends(get_context)) -> dict[str, str]:
    """Liveness. Touches no external dependency on purpose."""
    return {"status": "ok", "app": context.settings.app_name}


@router.get("/ready")
def ready(
    response: Response, context: ApplicationContext = Depends(get_context)
) -> dict[str, object]:
    """Readiness: can this instance actually answer a question right now?"""
    settings = context.settings
    checks: dict[str, str] = {}
    ok = True

    try:
        context.vector_store.health_check()
        checks["vector_store"] = "ok"
    except Exception as exc:
        checks["vector_store"] = f"unavailable: {type(exc).__name__}"
        ok = False

    try:
        # Same criteria the chat endpoint enforces and ingestion writes.
        index = context.index_status()
        if index.missing:
            checks["index"] = "missing: run `python -m app.cli ingest`"
            ok = False
        elif not index.compatible:
            checks["index"] = "incompatible with current configuration: re-index required"
            ok = False
        else:
            checks["index"] = "ok"
    except Exception as exc:
        checks["index"] = f"unreadable: {type(exc).__name__}"
        ok = False

    try:
        document_count = len(context.registry.load())
        checks["corpus_registry"] = "ok" if document_count else "empty: no documents ingested"
        ok = ok and document_count > 0
    except Exception as exc:
        checks["corpus_registry"] = f"unreadable: {type(exc).__name__}"
        document_count = 0
        ok = False

    # Pending files are visible warnings, not readiness failures.
    try:
        pending = context.registry.pending_files()
    except Exception:
        pending = []
    if pending:
        checks["corpus_files"] = (
            f"{len(pending)} file(s) in the corpus directory are not indexed: "
            f"run `python -m app.cli ingest`"
        )

    if not ok:
        response.status_code = 503

    return {
        "status": "ready" if ok else "not_ready",
        "checks": checks,
        "pending_files": pending,
        "documents": document_count,
        "chunks": (
            context.vector_store.count(settings.vector_store_collection)
            if checks.get("vector_store") == "ok"
            else 0
        ),
        "corpus_version": settings.corpus_version,
        "index_version": settings.index_version,
    }


@router.get("/corpus")
def corpus_contents(context: ApplicationContext = Depends(get_context)) -> dict[str, object]:
    """Return the corpus inventory recorded by the registry."""
    documents = context.registry.load()
    ordered = sorted(documents.values(), key=lambda r: r.document_title)
    return {
        "corpus_version": context.settings.corpus_version,
        # Surface source files that still need ingestion.
        "pending_files": context.registry.pending_files(),
        "documents": [
            {
                "document_id": record.document_id,
                "document_title": record.document_title,
                "source_type": record.source_type,
                "deliverable_id": record.deliverable_id,
                "page_count": record.page_count,
                "figure_count": record.figure_count,
            }
            for record in ordered
        ],
        "suggested_questions": suggested_questions(ordered),
    }


# Neutral wrapper for detected section headings.
_QUESTION_TEMPLATE = "What does the evidence say about {topic}?"
MAX_SUGGESTIONS = 4


def _as_question(topic: str) -> str:
    """Turn a section heading into a readable question."""
    cleaned = topic.strip()
    if cleaned.endswith("?"):
        return cleaned
    return _QUESTION_TEMPLATE.format(topic=cleaned)


def suggested_questions(records: list[DocumentRecord]) -> list[str]:
    """Build starter questions from indexed topics in document rotation."""
    questions: list[str] = []
    seen: set[str] = set()
    for index in range(max((len(record.topics) for record in records), default=0)):
        for record in records:
            if index >= len(record.topics):
                continue
            topic = record.topics[index]
            key = topic.lower()
            if key in seen:
                continue
            seen.add(key)
            questions.append(_as_question(topic))
            if len(questions) >= MAX_SUGGESTIONS:
                return questions
    return questions
