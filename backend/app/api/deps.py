"""Build and expose the application's shared dependency graph."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from app.config import Settings
from app.corpus.registry import CorpusRegistry
from app.onboarding.config_loader import load_onboarding_config
from app.providers.base import (
    EmbeddingProvider,
    IndexIncompatibleError,
    LanguageProvider,
    LLMProvider,
    RerankProvider,
    VectorStore,
    VisionProvider,
    incompatible_index_message,
    missing_index_message,
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
from app.schemas.chunks import IndexMetadata
from app.schemas.onboarding import OnboardingConfig
from app.services.multilingual_chat import MultilingualChatService


@dataclass(frozen=True, slots=True)
class IndexStatus:
    """What the running configuration expects versus what the store holds."""

    expected: IndexMetadata
    stored: IndexMetadata | None

    @property
    def missing(self) -> bool:
        return self.stored is None

    @property
    def compatible(self) -> bool:
        return (
            self.stored is not None
            and self.stored.compatibility_key() == self.expected.compatibility_key()
        )


@dataclass(slots=True)
class ApplicationContext:
    settings: Settings
    onboarding_config: OnboardingConfig
    llm: LLMProvider
    # Language routing through the configured LLM.
    language: LanguageProvider
    embeddings: EmbeddingProvider
    vector_store: VectorStore
    # None when vision is disabled.
    vision: VisionProvider | None
    # Query-time reranker; model changes need no re-ingestion.
    reranker: RerankProvider
    retriever: Retriever
    orchestrator: RagOrchestrator
    chat: MultilingualChatService
    registry: CorpusRegistry

    def expected_index_metadata(self) -> IndexMetadata:
        """The index identity this configuration requires. Mirrors ingestion."""
        settings = self.settings
        return IndexMetadata(
            collection=settings.vector_store_collection,
            embedding_provider=self.embeddings.provider_name,
            embedding_model=self.embeddings.model_name,
            embedding_dimensions=self.embeddings.dimensions,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            corpus_version=settings.corpus_version,
            index_version=settings.index_version,
        )

    def index_status(self) -> IndexStatus:
        expected = self.expected_index_metadata()
        stored = self.vector_store.get_index_metadata(expected.collection)
        return IndexStatus(expected=expected, stored=stored)

    def assert_index_compatible(self) -> None:
        """Raise IndexIncompatibleError unless the stored index fits this configuration.

        Readiness and answering share this one definition - and ingestion applies
        the same ``compatibility_key()`` when it writes - so the three can never
        disagree about what "compatible" means. Without the gate a never-built
        collection surfaced from the dense search as a raw 500, and an index built
        under another embedding model with the same dimensions would have been
        searched silently.
        """
        status = self.index_status()
        if status.missing:
            raise IndexIncompatibleError(missing_index_message(status.expected.collection))
        if not status.compatible:
            assert status.stored is not None
            raise IndexIncompatibleError(
                incompatible_index_message(status.stored, status.expected)
            )

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
