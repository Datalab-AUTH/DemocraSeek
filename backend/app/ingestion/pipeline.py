"""Ingest approved PDFs and images into the search store and registry.

Deterministic chunk IDs and file fingerprints make repeated runs idempotent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml

from app.config import Settings
from app.corpus.registry import CorpusRegistry
from app.ingestion import cleaning, pdf_extract
from app.ingestion.chunking import chunk_page
from app.ingestion.figures import build_figure_chunks, extract_figures
from app.ingestion.headings import extract_topics, looks_like_contents_page
from app.ingestion.lock import ingestion_lock
from app.ingestion.report import DocumentOutcome, IngestionReport, PageWarning
from app.ingestion.standalone_images import (
    humanise_filename,
    is_image_document,
    load_image_document,
)
from app.providers.base import EmbeddingProvider, VectorStore, VisionProvider
from app.schemas.chunks import Chunk, DocumentRecord, IndexMetadata, PageText
from app.schemas.figures import FigureRecord

logger = logging.getLogger(__name__)

# Optional document metadata sidecar.
METADATA_SIDECAR = "corpus.metadata.yaml"

# One metadata entry per source filename.
SidecarEntry = dict[str, str]


@dataclass(frozen=True)
class _PageChunks:
    """Text chunks and page-warning counts for one document."""

    chunks: list[Chunk]
    empty_pages: int
    ocr_review_pages: int


class IngestionService:
    def __init__(
        self,
        *,
        settings: Settings,
        embeddings: EmbeddingProvider,
        vector_store: VectorStore,
        registry: CorpusRegistry | None = None,
        vision: VisionProvider | None = None,
    ) -> None:
        self._settings = settings
        self._embeddings = embeddings
        self._store = vector_store
        self._vision = vision
        self._registry = registry or CorpusRegistry(settings.index_path, settings.corpus_path)

    # Public operations
    def index_metadata(self) -> IndexMetadata:
        settings = self._settings
        return IndexMetadata(
            collection=settings.vector_store_collection,
            embedding_provider=self._embeddings.provider_name,
            embedding_model=self._embeddings.model_name,
            embedding_dimensions=self._embeddings.dimensions,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            corpus_version=settings.corpus_version,
            index_version=settings.index_version,
        )

    def ingest(self, *, force: bool = False, only: str | None = None) -> IngestionReport:
        """Ingest approved files, optionally forcing or selecting one file."""
        with ingestion_lock(self._settings.index_path):
            return self._ingest_locked(force=force, only=only)

    def reindex(self) -> IngestionReport:
        """Rebuild the named index while holding the writer lock."""
        with ingestion_lock(self._settings.index_path):
            self._store.rebuild_index(self.index_metadata())
            for document_id in list(self._registry.load()):
                self._registry.delete_pages(document_id)
                self._registry.delete_figures(document_id)
            self._registry.save({})
            return self._ingest_locked(force=True, only=None)

    def remove_document(
        self, document_id: str, documents: dict[str, DocumentRecord] | None = None
    ) -> DocumentRecord:
        """Delete one document, taking the writer lock when needed."""
        if documents is None:
            with ingestion_lock(self._settings.index_path):
                return self._remove_locked(document_id, None)
        return self._remove_locked(document_id, documents)

    # Whole-run orchestration
    def _ingest_locked(self, *, force: bool, only: str | None) -> IngestionReport:
        """One ingestion run. The writer lock is already held."""
        report = self._new_report()
        self._store.ensure_index(self.index_metadata())

        corpus_dir = self._settings.corpus_path
        if not corpus_dir.is_dir():
            report.failures.append(
                {"filename": str(corpus_dir), "reason": "corpus directory does not exist"}
            )
            return report.finish()

        sidecar = self._load_sidecar(corpus_dir)
        source_files = self._discover_source_files(corpus_dir, only=only)
        report.files_discovered = len(source_files)

        documents = self._registry.load()
        ingested_ids: set[str] = set()

        for path in source_files:
            try:
                outcome = self._ingest_one(path, sidecar, documents, report, force=force)
            except Exception as exc:
                outcome = self._record_failure(path, exc, report)
            else:
                ingested_ids.add(outcome.document_id)
            report.documents.append(outcome)

        if only is None:
            self._remove_vanished_documents(documents, ingested_ids, report)

        self._registry.save(documents)
        return self._with_totals(report).finish()

    @staticmethod
    def _discover_source_files(corpus_dir: Path, *, only: str | None) -> list[Path]:
        """Approved files in the corpus directory, in a stable order."""
        files = sorted(
            (
                path
                for path in corpus_dir.iterdir()
                if path.is_file()
                and (path.suffix.lower() == ".pdf" or is_image_document(path))
            ),
            key=lambda path: path.name,
        )
        return [path for path in files if path.name == only] if only else files

    @staticmethod
    def _record_failure(path: Path, exc: Exception, report: IngestionReport) -> DocumentOutcome:
        """One file failing must not abandon the rest of the run."""
        # NB: "filename" is a reserved LogRecord attribute.
        logger.exception("ingestion_failed", extra={"pdf_filename": path.name})
        report.files_failed += 1
        report.failures.append({"filename": path.name, "reason": f"{type(exc).__name__}: {exc}"})
        return DocumentOutcome(
            document_id=pdf_extract.slugify_document_id(path.name),
            filename=path.name,
            status="failed",
            detail=type(exc).__name__,
        )

    def _remove_vanished_documents(
        self,
        documents: dict[str, DocumentRecord],
        ingested_ids: set[str],
        report: IngestionReport,
    ) -> None:
        """Remove missing sources after a full, unfiltered run."""
        for document_id in [known for known in documents if known not in ingested_ids]:
            removed = self._remove_locked(document_id, documents)
            report.files_removed += 1
            report.documents.append(
                DocumentOutcome(
                    document_id=document_id,
                    filename=removed.filename,
                    status="removed",
                    detail="source file no longer present in the corpus directory",
                )
            )

    def _remove_locked(
        self, document_id: str, documents: dict[str, DocumentRecord] | None
    ) -> DocumentRecord:
        owns_registry = documents is None
        registry_documents = documents if documents is not None else self._registry.load()
        record = registry_documents.pop(document_id, None)
        if record is None:
            raise KeyError(document_id)
        self._store.delete_document(self._settings.vector_store_collection, document_id)
        self._registry.delete_pages(document_id)
        self._registry.delete_figures(document_id)
        if owns_registry:
            self._registry.save(registry_documents)
        return record

    # One document
    def _ingest_one(
        self,
        path: Path,
        sidecar: dict[str, SidecarEntry],
        documents: dict[str, DocumentRecord],
        report: IngestionReport,
        *,
        force: bool,
    ) -> DocumentOutcome:
        """Extract, chunk, embed and store a single approved file."""
        document_id = pdf_extract.slugify_document_id(path.name)
        checksum = pdf_extract.compute_checksum(path)
        fingerprint = self._settings.index_fingerprint
        existing = documents.get(document_id)

        if not force and self._is_unchanged(existing, checksum, fingerprint):
            return self._skipped_outcome(document_id, path, existing, report)

        entry = sidecar.get(path.name, {})
        title = self._resolve_title(path, entry)
        metadata_template = self._metadata_template(document_id, checksum, title, path.name, entry)

        pages, figures = self._read_source(path, document_id=document_id, title=title)
        text = self._chunk_pages(pages, document_id, metadata_template, report)
        figure_chunks = build_figure_chunks(
            figures,
            figures_dir=self._registry.figures_dir,
            vision=self._vision,
            metadata_template=metadata_template,
        )
        chunks = text.chunks + figure_chunks

        self._replace_stored_chunks(document_id, chunks)
        self._registry.save_pages(document_id, pages)
        documents[document_id] = self._document_record(
            document_id=document_id,
            path=path,
            checksum=checksum,
            fingerprint=fingerprint,
            title=title,
            entry=entry,
            pages=pages,
            chunk_count=len(chunks),
            figure_count=len(figures),
        )

        if existing is not None:
            report.files_updated += 1
        else:
            report.files_ingested += 1
        return DocumentOutcome(
            document_id=document_id,
            filename=path.name,
            status="updated" if existing is not None else "ingested",
            page_count=len(pages),
            chunk_count=len(chunks),
            figure_count=len(figures),
            retrievable_figures=len(figure_chunks),
            empty_pages=text.empty_pages,
            ocr_review_pages=text.ocr_review_pages,
        )

    @staticmethod
    def _is_unchanged(
        existing: DocumentRecord | None, checksum: str, fingerprint: str
    ) -> bool:
        """True when neither the file nor the way we index it has changed."""
        return (
            existing is not None
            and existing.document_checksum == checksum
            and existing.index_fingerprint == fingerprint
        )

    @staticmethod
    def _skipped_outcome(
        document_id: str, path: Path, existing: DocumentRecord | None, report: IngestionReport
    ) -> DocumentOutcome:
        report.files_skipped_unchanged += 1
        return DocumentOutcome(
            document_id=document_id,
            filename=path.name,
            status="skipped_unchanged",
            page_count=existing.page_count if existing else 0,
            chunk_count=existing.chunk_count if existing else 0,
        )

    @staticmethod
    def _resolve_title(path: Path, entry: SidecarEntry) -> str:
        """The operator's title wins; then the PDF's own; then the filename."""
        if entry.get("document_title"):
            return entry["document_title"]
        if is_image_document(path):
            return humanise_filename(path)
        return pdf_extract.read_pdf_title(path) or path.stem

    def _metadata_template(
        self, document_id: str, checksum: str, title: str, filename: str, entry: SidecarEntry
    ) -> dict[str, object]:
        """Fields every chunk of this document carries, so a citation is complete."""
        settings = self._settings
        return {
            "document_id": document_id,
            "document_checksum": checksum,
            "document_title": title,
            "filename": filename,
            "deliverable_id": entry.get("deliverable_id", ""),
            "publication_date": entry.get("publication_date", ""),
            "corpus_version": settings.corpus_version,
            "index_version": settings.index_version,
            "embedding_provider": self._embeddings.provider_name,
            "embedding_model": self._embeddings.model_name,
            "embedding_dimensions": self._embeddings.dimensions,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
        }

    def _read_source(
        self, path: Path, *, document_id: str, title: str
    ) -> tuple[list[PageText], list[FigureRecord]]:
        """Read pages and figures, storing images before vision processing."""
        self._registry.delete_figures(document_id)
        if is_image_document(path):
            # A standalone image is a one-page visual document.
            pages, figures = load_image_document(
                path,
                document_id=document_id,
                title=title,
                output_dir=self._registry.figures_dir,
            )
        else:
            pages = cleaning.clean_pages(pdf_extract.extract_pages(path))
            figures = extract_figures(
                path, pages, document_id=document_id, output_dir=self._registry.figures_dir
            )
        self._registry.save_figures(document_id, figures)
        return pages, figures

    def _chunk_pages(
        self,
        pages: list[PageText],
        document_id: str,
        metadata_template: dict[str, object],
        report: IngestionReport,
    ) -> _PageChunks:
        settings = self._settings
        chunks: list[Chunk] = []
        empty_pages = 0
        ocr_review_pages = 0

        for page in pages:
            if page.is_empty:
                empty_pages += 1
            if page.needs_ocr_review:
                ocr_review_pages += 1
                report.page_warnings.append(
                    PageWarning(
                        document_id=document_id,
                        page_number=page.page_number,
                        reason=page.ocr_reason,
                    )
                )
            # Contents pages add noisy headings and page numbers to retrieval.
            if looks_like_contents_page(page.text):
                continue
            chunks.extend(
                chunk_page(
                    page,
                    document_id=document_id,
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap,
                    metadata_template=metadata_template,
                )
            )

        return _PageChunks(
            chunks=chunks, empty_pages=empty_pages, ocr_review_pages=ocr_review_pages
        )

    def _replace_stored_chunks(self, document_id: str, chunks: list[Chunk]) -> None:
        """Replace all chunks so updates cannot leave orphaned rows."""
        collection = self._settings.vector_store_collection
        self._store.delete_document(collection, document_id)
        if chunks:
            vectors = self._embeddings.embed_documents([chunk.chunk_text for chunk in chunks])
            self._store.upsert_chunks(collection, chunks, vectors)

    def _document_record(
        self,
        *,
        document_id: str,
        path: Path,
        checksum: str,
        fingerprint: str,
        title: str,
        entry: SidecarEntry,
        pages: list[PageText],
        chunk_count: int,
        figure_count: int,
    ) -> DocumentRecord:
        settings = self._settings
        return DocumentRecord(
            document_id=document_id,
            document_checksum=checksum,
            document_title=title,
            filename=path.name,
            document_type="image" if is_image_document(path) else "pdf",
            deliverable_id=entry.get("deliverable_id", ""),
            publication_date=entry.get("publication_date", ""),
            page_count=len(pages),
            chunk_count=chunk_count,
            figure_count=figure_count,
            topics=extract_topics([page.text for page in pages]),
            corpus_version=settings.corpus_version,
            index_version=settings.index_version,
            index_fingerprint=fingerprint,
            ingested_at=datetime.now(UTC).isoformat(),
        )

    # Reporting
    def _new_report(self) -> IngestionReport:
        settings = self._settings
        return IngestionReport(
            corpus_path=str(settings.corpus_path),
            corpus_version=settings.corpus_version,
            index_version=settings.index_version,
            index_fingerprint=settings.index_fingerprint,
            collection=settings.vector_store_collection,
            embedding_provider=self._embeddings.provider_name,
            embedding_model=self._embeddings.model_name,
            embedding_dimensions=self._embeddings.dimensions,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            vision_provider=self._vision.provider_name if self._vision else "none",
            vision_model=self._vision.model_name if self._vision else "",
        )

    @staticmethod
    def _with_totals(report: IngestionReport) -> IngestionReport:
        report.total_pages = sum(doc.page_count for doc in report.documents)
        report.total_chunks = sum(doc.chunk_count for doc in report.documents)
        report.total_figures = sum(doc.figure_count for doc in report.documents)
        report.total_retrievable_figures = sum(doc.retrievable_figures for doc in report.documents)
        return report

    @staticmethod
    def _load_sidecar(corpus_dir: Path) -> dict[str, SidecarEntry]:
        """Read optional per-file metadata. Missing values stay empty."""
        path = corpus_dir / METADATA_SIDECAR
        if not path.is_file():
            return {}
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        documents = raw.get("documents", {})
        if not isinstance(documents, dict):
            return {}
        return {
            str(filename): {str(key): str(value) for key, value in (entry or {}).items()}
            for filename, entry in documents.items()
        }
