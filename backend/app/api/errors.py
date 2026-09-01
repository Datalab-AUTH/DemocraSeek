"""Structured error handling.

Clients get a stable error code, a safe message and the request id. Internal
detail (stack traces, provider messages, connection strings) stays in the log.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.corpus.registry import DocumentNotFoundError
from app.onboarding.compiler import PolicyVersionMismatchError, UnknownCodeError
from app.providers.base import IndexIncompatibleError, ProviderError
from app.rag.query import InvalidQuestionError

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int) -> None:
        super().__init__("rate limit exceeded")
        self.retry_after = retry_after


def _body(request: Request, error: str, detail: str) -> dict[str, str]:
    return {
        "error": error,
        "detail": detail,
        "request_id": getattr(request.state, "request_id", "-"),
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(InvalidQuestionError)
    async def _invalid_question(request: Request, exc: InvalidQuestionError) -> JSONResponse:
        return JSONResponse(status_code=400, content=_body(request, "invalid_question", str(exc)))

    @app.exception_handler(UnknownCodeError)
    async def _unknown_code(request: Request, exc: UnknownCodeError) -> JSONResponse:
        return JSONResponse(status_code=400, content=_body(request, "unknown_code", str(exc)))

    @app.exception_handler(PolicyVersionMismatchError)
    async def _policy_version(
        request: Request, exc: PolicyVersionMismatchError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409, content=_body(request, "policy_version_mismatch", str(exc))
        )

    @app.exception_handler(DocumentNotFoundError)
    async def _document_missing(request: Request, exc: DocumentNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=_body(request, "document_not_found", "No such document in the corpus."),
        )

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limited(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content=_body(request, "rate_limited", "Too many requests. Please wait and retry."),
            headers={"Retry-After": str(exc.retry_after)},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_body(request, "validation_error", "The request body was not valid."),
        )

    @app.exception_handler(IndexIncompatibleError)
    async def _index_incompatible(
        request: Request, exc: IndexIncompatibleError
    ) -> JSONResponse:
        logger.error("index_incompatible", extra={"error_category": "index_incompatible"})
        return JSONResponse(
            status_code=503,
            content=_body(
                request,
                "index_incompatible",
                "The search index does not match the current configuration. "
                "An operator must re-index the corpus.",
            ),
        )

    @app.exception_handler(ProviderError)
    async def _provider(request: Request, exc: ProviderError) -> JSONResponse:
        logger.error("provider_error", extra={"error_category": "provider"})
        return JSONResponse(
            status_code=503,
            content=_body(
                request, "provider_unavailable", "An upstream service is currently unavailable."
            ),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", extra={"error_category": "unhandled"})
        return JSONResponse(
            status_code=500,
            content=_body(request, "internal_error", "An unexpected error occurred."),
        )
