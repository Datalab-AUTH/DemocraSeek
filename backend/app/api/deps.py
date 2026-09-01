"""Application wiring.

A plain object built once at startup and hung on ``app.state``. No dependency
injection container, no service locator: the object graph is small enough to
read in one screen, which is the point.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from app.config import Settings
from app.corpus.registry import CorpusRegistry
from app.onboarding.config_loader import load_onboarding_config
from app.providers.base import (
    EmbeddingProvider,
    LanguageProvider,
    LLMProvider,
    RerankProvider,
    VectorStore,
    VisionProvider,
)
from app.providers.factory import (
    build_embeddings,
    build_language_provider,
    build_llm,
    build_reranker,
    build_vector_store,
    build_vision,
)
from app.rag.orchestrator import RagOrchestrator
from app.rag.retriever import Retriever
from app.schemas.onboarding import OnboardingConfig
from app.services.multilingual_chat import MultilingualChatService


@dataclass(slots=True)
class ApplicationContext:
    settings: Settings
    onboarding_config: OnboardingConfig
    llm: LLMProvider
    #: Detects/translates around the English RAG core using the configured LLM.
    language: LanguageProvider
    embeddings: EmbeddingProvider
    vector_store: VectorStore
    #: None when figure descriptions are switched off (VISION_PROVIDER=none).
    vision: VisionProvider | None
    #: Mandatory query-time reranker. It is not part of the index fingerprint
    #: and changing its model never needs a re-ingest.
    reranker: RerankProvider
    retriever: Retriever
    orchestrator: RagOrchestrator
    chat: MultilingualChatService
    registry: CorpusRegistry

    def close(self) -> None:
        for component in (
            self.llm,
            self.embeddings,
            self.vector_store,
            self.vision,
            self.reranker,
        ):
            if component is None:
                continue
            closer = getattr(component, "close", None)
            if callable(closer):
                closer()


def build_context(settings: Settings) -> ApplicationContext:
    onboarding_config = load_onboarding_config(settings.onboarding_config_path)
    llm = build_llm(settings)
    language = build_language_provider(settings, llm)
    embeddings = build_embeddings(settings)
    vector_store = build_vector_store(settings)
    vision = build_vision(settings)
    reranker = build_reranker(settings)
    registry = CorpusRegistry(settings.index_path, settings.corpus_path)

    retriever = Retriever(
        embeddings=embeddings,
        vector_store=vector_store,
        collection=settings.vector_store_collection,
        top_k=settings.retrieval_top_k,
        score_threshold=settings.retrieval_score_threshold,
        max_context_tokens=settings.retrieval_max_context_tokens,
        reranker=reranker,
        candidate_k=settings.retrieval_candidate_k,
    )
    orchestrator = RagOrchestrator(
        llm=llm,
        retriever=retriever,
        onboarding_config=onboarding_config,
        max_user_input_chars=settings.max_user_input_chars,
        max_conversation_messages=settings.max_conversation_messages,
        registry=registry,
    )
    chat = MultilingualChatService(
        rag=orchestrator,
        language=language,
        max_user_input_chars=settings.max_user_input_chars,
        max_conversation_messages=settings.max_conversation_messages,
    )
    return ApplicationContext(
        settings=settings,
        onboarding_config=onboarding_config,
        llm=llm,
        language=language,
        embeddings=embeddings,
        vector_store=vector_store,
        vision=vision,
        reranker=reranker,
        retriever=retriever,
        orchestrator=orchestrator,
        chat=chat,
        registry=registry,
    )


def get_context(request: Request) -> ApplicationContext:
    context: ApplicationContext = request.app.state.context
    return context
