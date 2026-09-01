"""Neutral internal schemas for corpus content.

These types are provider-agnostic on purpose: no adapter (LLM, embedding,
vector store) may leak its own objects past this boundary.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

#: "text" comes from the page's text layer. "figure" is a figure's caption plus
#: a derived description, which is retrievable evidence but NOT document text.
Modality = Literal["text", "figure"]


class PageText(BaseModel):
    """One extracted PDF page, before chunking."""

    model_config = ConfigDict(frozen=True)

    page_number: int = Field(ge=1)
    text: str
    char_count: int
    is_empty: bool
    needs_ocr_review: bool
    ocr_reason: str = ""


class ChunkMetadata(BaseModel):
    """Metadata attached to every stored chunk.

    Optional fields (``deliverable_id``, ``publication_date``, ``section``)
    stay empty when they cannot be determined reliably. They are never invented.
    """

    document_id: str
    document_checksum: str
    document_title: str
    filename: str
    deliverable_id: str = ""
    publication_date: str = ""
    page_number: int = Field(ge=1)
    section: str = ""
    chunk_id: str
    #: What kind of evidence this chunk is. Figure chunks are rendered and
    #: cited differently, because part of their text is derived, not quoted.
    modality: Modality = "text"
    #: Set only on figure chunks: which figure this chunk describes.
    figure_id: str = ""
    #: Provenance of a figure chunk's description, e.g. "vision:qwen2.5vl:7b"
    #: or "caption_only". Empty for text chunks.
    description_source: str = ""
    corpus_version: str
    index_version: str
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    chunk_size: int
    chunk_overlap: int


class Chunk(BaseModel):
    """A retrievable unit: text plus its full provenance."""

    chunk_id: str
    chunk_text: str
    metadata: ChunkMetadata

    def to_record(self) -> dict[str, object]:
        """Flat representation used by the ingestion report and fixtures."""
        return {"chunk_text": self.chunk_text, **self.metadata.model_dump()}


class RetrievedChunk(BaseModel):
    """A chunk returned by retrieval, with the scores that placed it there."""

    chunk: Chunk
    #: Cosine similarity from the vector store, in [-1, 1]. This is the only
    #: score compared against RETRIEVAL_SCORE_THRESHOLD. It is 0.0 for a chunk
    #: that lexical search found and vector search did not, meaning "no cosine
    #: was computed", not "dissimilar".
    score: float
    #: Cross-encoder relevance, when reranking ran. An unbounded logit on a
    #: different scale from ``score``: useful for ordering and for logs, never
    #: comparable with the threshold.
    rerank_score: float | None = None


class IndexMetadata(BaseModel):
    """Identity of a named index. Guards against mixing incompatible vectors."""

    collection: str
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    chunk_size: int
    chunk_overlap: int
    corpus_version: str
    index_version: str

    def compatibility_key(self) -> tuple[str, str, int, int, int, str]:
        """Fields that must match for stored vectors to remain usable.

        ``corpus_version`` is deliberately excluded: adding documents to the
        corpus does not invalidate existing vectors.
        """
        return (
            self.embedding_provider,
            self.embedding_model,
            self.embedding_dimensions,
            self.chunk_size,
            self.chunk_overlap,
            self.index_version,
        )


#: "pdf" is a paginated text document; "image" is a standalone image file
#: ingested as a one-page document whose only content is the picture.
DocumentType = Literal["pdf", "image"]


class DocumentRecord(BaseModel):
    """One ingested document, as tracked by the corpus registry."""

    document_id: str
    document_checksum: str
    document_title: str
    filename: str
    document_type: DocumentType = "pdf"
    deliverable_id: str = ""
    publication_date: str = ""
    page_count: int
    chunk_count: int
    figure_count: int = 0
    #: Subject headings detected in this document. Used to suggest starter
    #: questions that are guaranteed to have something behind them.
    topics: list[str] = []
    corpus_version: str
    index_version: str
    index_fingerprint: str
    ingested_at: str
