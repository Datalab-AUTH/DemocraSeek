"""Narrow interfaces for replaceable external providers."""

from __future__ import annotations

from typing import Protocol

from app.schemas.chunks import Chunk, IndexMetadata, RetrievedChunk
from app.schemas.language import LanguageRoute


class ProviderError(RuntimeError):
    """Any failure originating in an external provider."""


class IndexIncompatibleError(RuntimeError):
    """Stored vectors cannot be used with the current configuration."""


def missing_index_message(collection: str) -> str:
    return f"Index {collection!r} has not been built: run `python -m app.cli ingest`."


def incompatible_index_message(existing: IndexMetadata, requested: IndexMetadata) -> str:
    return (
        f"Index {existing.collection!r} was built with "
        f"(provider={existing.embedding_provider}, model={existing.embedding_model}, "
        f"dims={existing.embedding_dimensions}, chunk_size={existing.chunk_size}, "
        f"overlap={existing.chunk_overlap}, index_version={existing.index_version}) but the "
        f"current configuration is (provider={requested.embedding_provider}, "
        f"model={requested.embedding_model}, dims={requested.embedding_dimensions}, "
        f"chunk_size={requested.chunk_size}, overlap={requested.chunk_overlap}, "
        f"index_version={requested.index_version}). Mixing them is not allowed. "
        f"Run `python -m app.cli reindex --yes` to rebuild from the approved corpus."
    )


# LLM
class LLMProvider(Protocol):
    """Generate grounded answers as JSON text."""

    @property
    def model_name(self) -> str: ...

    @property
    def provider_name(self) -> str: ...

    def validate_configuration(self) -> None:
        """Raise ProviderError if this adapter cannot possibly work."""
        ...

    def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        """Return raw JSON text without parsing or repair."""
        ...


# Embeddings
class EmbeddingProvider(Protocol):
    @property
    def model_name(self) -> str: ...

    @property
    def provider_name(self) -> str: ...

    @property
    def dimensions(self) -> int: ...

    def validate_configuration(self) -> None: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed corpus chunks. Batching is handled inside the adapter."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed a single user query."""
        ...


# Vision
class VisionProvider(Protocol):
    """Describe figures during ingestion; output is derived evidence."""

    @property
    def model_name(self) -> str: ...

    @property
    def provider_name(self) -> str: ...

    def validate_configuration(self) -> None: ...

    def describe_image(self, image_png: bytes, *, context: str = "") -> str:
        """Describe one figure, or return empty text when nothing useful is found."""
        ...


# Vector store
class VectorStore(Protocol):
    @property
    def provider_name(self) -> str: ...

    def ensure_index(self, metadata: IndexMetadata) -> IndexMetadata:
        """Create the index or reject incompatible stored metadata."""
        ...

    def get_index_metadata(self, collection: str) -> IndexMetadata | None: ...

    def upsert_chunks(
        self, collection: str, chunks: list[Chunk], embeddings: list[list[float]]
    ) -> int:
        """Insert or replace chunks keyed by ``chunk_id``. Returns rows written."""
        ...

    def delete_document(self, collection: str, document_id: str) -> int:
        """Remove every chunk of one document. Returns rows deleted."""
        ...

    def search(
        self, collection: str, query_embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]:
        """Cosine-similarity search. Scores are in [-1, 1], higher is better."""
        ...


    def lexical_search(
        self, collection: str, query: str, top_k: int
    ) -> list[RetrievedChunk]:
        """Return BM25 hits; lexical-only hits keep cosine ``score=0.0``."""
        ...

    def rebuild_index(self, metadata: IndexMetadata) -> None:
        """Drop and recreate the named index. Used by the re-index workflow."""
        ...

    def count(self, collection: str) -> int: ...

    def health_check(self) -> None:
        """Raise ProviderError if the store is unreachable."""
        ...

    def close(self) -> None: ...


# Language
class LanguageProvider(Protocol):
    """Language detection and translation around the English RAG pipeline."""

    @property
    def model_name(self) -> str: ...

    @property
    def provider_name(self) -> str: ...

    def validate_configuration(self) -> None: ...

    def route_to_english(self, text: str) -> LanguageRoute:
        """Detect the dominant language and translate ``text`` to English."""
        ...

    def translate_answer(
        self, text: str, *, language_code: str, language_name: str
    ) -> str:
        """Translate an English answer while preserving citation markers."""
        ...


# Reranking
class RerankProvider(Protocol):
    """Score query-document pairs for ordering, never threshold gating."""

    @property
    def model_name(self) -> str: ...

    @property
    def provider_name(self) -> str: ...

    def validate_configuration(self) -> None: ...

    def rerank(self, query: str, documents: list[str]) -> list[float]:
        """Return one relevance score per document without reordering."""
        ...
