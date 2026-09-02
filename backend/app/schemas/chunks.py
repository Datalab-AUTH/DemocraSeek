"""Provider-neutral schemas for corpus content and retrieval."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Text is extracted; figure content may include a derived description.
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
    """Trusted provenance and index metadata for a stored chunk."""

    document_id: str
    document_checksum: str
    document_title: str
    filename: str
    deliverable_id: str = ""
    publication_date: str = ""
    page_number: int = Field(ge=1)
    section: str = ""
    chunk_id: str
    # Evidence type: extracted text or a figure description.
    modality: Modality = "text"
    # Figure ID, set only for figure chunks.
    figure_id: str = ""
    # Figure-description source; empty for text chunks.
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
        """Return a flat record for reporting or export."""
        return {"chunk_text": self.chunk_text, **self.metadata.model_dump()}


class RetrievedChunk(BaseModel):
    """A chunk returned by retrieval, with the scores that placed it there."""

    chunk: Chunk
    # Cosine similarity; zero also marks lexical-only hits.
    score: float
    # Cross-encoder score used only for ordering.
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
        """Return fields that must match for stored vectors to stay valid."""
        return (
            self.embedding_provider,
            self.embedding_model,
            self.embedding_dimensions,
            self.chunk_size,
            self.chunk_overlap,
            self.index_version,
        )


# Source type: paginated PDF or one-page standalone image.
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
    # Indexed headings used for starter questions.
    topics: list[str] = []
    corpus_version: str
    index_version: str
    index_fingerprint: str
    ingested_at: str
