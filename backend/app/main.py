"""FastAPI application factory.

Endpoints are synchronous (``def``, not ``async def``). FastAPI runs them in a
threadpool, which suits the blocking HTTP and database calls this application
makes and keeps the RAG flow readable top to bottom. Streaming is therefore not
implemented; it is optional in the requirements and would add an async path
through every layer for no current benefit.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_chat, routes_health, routes_onboarding, routes_sources
from app.api.deps import build_context
from app.api.errors import register_exception_handlers
from app.api.middleware import request_context_middleware
from app.api.rate_limit import RateLimiter
from app.config import Settings, get_settings
from app.logging_setup import configure_logging
from app.providers.factory import log_selected_providers

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.context = build_context(settings)
        app.state.rate_limiter = RateLimiter(
            max_requests=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )
        log_selected_providers(settings)
        logger.info("application_started", extra={"app_env": settings.app_env})
        try:
            yield
        finally:
            app.state.context.close()
            logger.info("application_stopped")

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Grounded, citation-verified answers from the approved INNOVADE "
            "knowledge base."
        ),
        lifespan=lifespan,
    )

    app.middleware("http")(request_context_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(settings),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

    register_exception_handlers(app)
    app.include_router(routes_health.router)
    app.include_router(routes_onboarding.router)
    app.include_router(routes_chat.router)
    app.include_router(routes_sources.router)
    return app


def _allowed_origins(settings: Settings) -> list[str]:
    """Development serves the frontend from Vite; production from one origin."""
    if settings.app_env == "production":
        return [settings.app_base_url] if settings.app_base_url else []
    return ["http://localhost:5173", "http://127.0.0.1:5173", settings.app_base_url]


# Started with `uvicorn app.main:create_app --factory`. There is deliberately no
# module-level app instance: importing this module must not read configuration
# or build providers as a side effect.
