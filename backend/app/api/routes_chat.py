"""The chat endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.deps import ApplicationContext, get_context
from app.api.errors import RateLimitExceeded
from app.api.rate_limit import RateLimiter
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    request: Request,
    context: ApplicationContext = Depends(get_context),
) -> ChatResponse:
    limiter: RateLimiter = request.app.state.rate_limiter
    key = _client_key(request)
    if not limiter.check(key):
        raise RateLimitExceeded(limiter.retry_after(key))

    result = context.chat.answer(
        question=payload.question,
        profile=payload.profile,
        history=payload.history,
    )
    return ChatResponse(
        **result.model_dump(),
        request_id=getattr(request.state, "request_id", "-"),
    )
