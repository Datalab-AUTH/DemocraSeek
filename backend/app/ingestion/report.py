"""Machine-readable and human-readable ingestion reports."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class PageWarning(BaseModel):
    document_id: str
    page_number: int
    reason: str


class DocumentOutcome(BaseModel):
    document_id: str
    filename: str
    status: str  # ingested | updated | skipped_unchanged | removed | failed
    page_count: int = 0
    chunk_count: int = 0
    #: Figures kept after filtering out logos, rules and decorations.
    figure_count: int = 0
    #: Figures that became searchable evidence (had a caption or a description).
    retrievable_figures: int = 0
    empty_pages: int = 0
    ocr_review_pages: int = 0
    detail: str = ""


class IngestionReport(BaseModel):
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str = ""
    corpus_path: str = ""
    corpus_version: str = ""
    index_version: str = ""
    index_fingerprint: str = ""
    collection: str = ""
    embedding_provider: str = ""
    embedding_model: str = ""
    embedding_dimensions: int = 0
    chunk_size: int = 0
    chunk_overlap: int = 0

    files_discovered: int = 0
    files_ingested: int = 0
    files_updated: int = 0
    files_skipped_unchanged: int = 0
    files_removed: int = 0
    files_failed: int = 0

    total_pages: int = 0
    total_chunks: int = 0
    total_figures: int = 0
    total_retrievable_figures: int = 0
    vision_provider: str = "none"
    vision_model: str = ""

    documents: list[DocumentOutcome] = []
    page_warnings: list[PageWarning] = []
    failures: list[dict[str, str]] = []

    def finish(self) -> IngestionReport:
        self.finished_at = datetime.now(UTC).isoformat()
        return self

    def write(self, report_dir: Path) -> tuple[Path, Path]:
        """Write JSON and text versions. Returns both paths."""
        report_dir.mkdir(parents=True, exist_ok=True)
        stamp = self.started_at.replace(":", "").replace("-", "").split(".")[0]
        json_path = report_dir / f"ingestion-{stamp}.json"
        text_path = report_dir / f"ingestion-{stamp}.txt"
        json_path.write_text(
            json.dumps(self.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        text_path.write_text(self.render_text(), encoding="utf-8")
        return json_path, text_path

    def render_text(self) -> str:
        lines = [
            "DemocraSeek ingestion report",
            "=" * 60,
            f"started            : {self.started_at}",
            f"finished           : {self.finished_at}",
            f"corpus path        : {self.corpus_path}",
            f"corpus version     : {self.corpus_version}",
            f"index version      : {self.index_version}",
            f"collection         : {self.collection}",
            f"embedding          : {self.embedding_provider}/{self.embedding_model} "
            f"({self.embedding_dimensions}d)",
            f"chunking           : size={self.chunk_size} overlap={self.chunk_overlap}",
            f"figure descriptions: {self.vision_provider}"
            + (f"/{self.vision_model}" if self.vision_model else ""),
            f"index fingerprint  : {self.index_fingerprint}",
            "",
            "Summary",
            "-" * 60,
            f"files discovered   : {self.files_discovered}",
            f"files ingested     : {self.files_ingested}",
            f"files updated      : {self.files_updated}",
            f"skipped unchanged  : {self.files_skipped_unchanged}",
            f"files removed      : {self.files_removed}",
            f"files failed       : {self.files_failed}",
            f"total pages        : {self.total_pages}",
            f"total chunks       : {self.total_chunks}",
            f"figures kept       : {self.total_figures}",
            f"figures searchable : {self.total_retrievable_figures}",
            "",
            "Documents",
            "-" * 60,
        ]
        for doc in self.documents:
            lines.append(
                f"[{doc.status:<18}] {doc.filename} "
                f"(id={doc.document_id}, pages={doc.page_count}, chunks={doc.chunk_count}, "
                f"figures={doc.figure_count}/{doc.retrievable_figures} searchable, "
                f"empty={doc.empty_pages}, ocr_review={doc.ocr_review_pages})"
                + (f" - {doc.detail}" if doc.detail else "")
            )
        if self.page_warnings:
            lines += ["", "Pages that may require OCR review", "-" * 60]
            lines += [
                f"{warning.document_id} p.{warning.page_number}: {warning.reason}"
                for warning in self.page_warnings
            ]
        if self.failures:
            lines += ["", "Failures", "-" * 60]
            lines += [
                f"{item.get('filename', '?')}: {item.get('reason', '')}"
                for item in self.failures
            ]
        return "\n".join(lines) + "\n"
