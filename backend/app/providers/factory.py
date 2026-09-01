"""Build configured providers through explicit adapter factories."""

from __future__ import annotations

import logging

from app.config import Settings
from app.providers.base import (
    EmbeddingProvider,
    LanguageProvider,
    LLMProvider,
    RerankProvider,
    VectorStore,
    VisionProvider,
)
from app.providers.embeddings_openai_compatible import OpenAICompatibleEmbeddings
from app.providers.language_llm import LLMLanguageProvider
from app.providers.llm_openai_compatible import OpenAICompatibleLLM
from app.providers.vectorstore_pgvector import PgVectorStore
from app.providers.vision_openai_compatible import OpenAICompatibleVision

logger = logging.getLogger(__name__)


def build_llm(settings: Settings) -> LLMProvider:
    provider: LLMProvider = OpenAICompatibleLLM(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_output_tokens=settings.llm_max_output_tokens,
        timeout_seconds=settings.llm_timeout_seconds,
    )
    provider.validate_configuration()
    return provider


def build_language_provider(settings: Settings, llm: LLMProvider) -> LanguageProvider:
    """Use the answering LLM for language routing and translation."""
    provider: LanguageProvider = LLMLanguageProvider(llm)
    provider.validate_configuration()
    return provider


def build_embeddings(settings: Settings) -> EmbeddingProvider:
    provider: EmbeddingProvider = OpenAICompatibleEmbeddings(
        base_url=settings.embedding_base_url,
        api_key=settings.embedding_api_key,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        batch_size=settings.embedding_batch_size,
    )
    provider.validate_configuration()
    return provider


def build_vision(settings: Settings) -> VisionProvider | None:
    """Return None when figure descriptions are switched off."""
    if settings.vision_provider == "none":
        return None
    if settings.vision_provider == "openai_compatible":
        provider: VisionProvider = OpenAICompatibleVision(
            base_url=settings.vision_base_url,
            api_key=settings.vision_api_key,
            model=settings.vision_model,
            timeout_seconds=settings.vision_timeout_seconds,
            max_description_chars=settings.vision_max_description_chars,
        )
    else:
        raise ValueError(f"Unknown VISION_PROVIDER: {settings.vision_provider!r}")
    provider.validate_configuration()
    return provider


def build_reranker(settings: Settings) -> RerankProvider:
    """Build the mandatory query-time reranker."""
    # Delay the expensive PyTorch import until a query process starts.
    from app.providers.rerank_cross_encoder import CrossEncoderReranker

    provider: RerankProvider = CrossEncoderReranker(model=settings.rerank_model)
    provider.validate_configuration()
    return provider


def build_vector_store(settings: Settings) -> VectorStore:
    return PgVectorStore(dsn=settings.vector_store_url)


def log_selected_providers(settings: Settings) -> None:
    """Log provider identity. Never logs URLs or credentials."""
    logger.info("providers_selected", extra={"providers": settings.safe_provider_summary()})
