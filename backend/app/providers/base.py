"""Narrow interfaces for replaceable external providers."""

from __future__ import annotations

from typing import Protocol

from app.schemas.chunks import Chunk, IndexMetadata, RetrievedChunk
from app.schemas.language import LanguageRoute


class ProviderError(RuntimeError):
    """Any failure originating in an external provider."""


class IndexIncompatibleError(RuntimeError):
    """Stored vectors cannot be used with the current configuration."""


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

    def replace_document_chunks(
        self,
        collection: str,
        document_id: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> int:
        """Replace one document's chunks atomically. Returns rows written."""
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
