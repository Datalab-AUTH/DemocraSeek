"""Store derived document, page and figure records for safe source lookup."""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.schemas.chunks import DocumentRecord, PageText
from app.schemas.figures import FigureRecord


class DocumentNotFoundError(LookupError):
    """The requested document id is not in the registry."""


def _write_atomic(path: Path, content: str) -> None:
    """Replace a file atomically so readers never see partial JSON."""
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


class CorpusRegistry:
    def __init__(self, index_path: Path, corpus_path: Path) -> None:
        self._index_path = index_path
        self._corpus_path = corpus_path
        self._documents_file = index_path / "documents.json"
        self._pages_dir = index_path / "pages"

    # Documents
    def load(self) -> dict[str, DocumentRecord]:
        if not self._documents_file.exists():
            return {}
        raw = json.loads(self._documents_file.read_text(encoding="utf-8"))
        return {
            doc_id: DocumentRecord.model_validate(record) for doc_id, record in raw.items()
        }

    def save(self, documents: dict[str, DocumentRecord]) -> None:
        self._index_path.mkdir(parents=True, exist_ok=True)
        payload = {
            doc_id: record.model_dump() for doc_id, record in sorted(documents.items())
        }
        _write_atomic(
            self._documents_file,
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        )

    def get(self, document_id: str) -> DocumentRecord:
        record = self.load().get(document_id)
        if record is None:
            raise DocumentNotFoundError(document_id)
        return record

    # Pages
    def save_pages(self, document_id: str, pages: list[PageText]) -> None:
        self._pages_dir.mkdir(parents=True, exist_ok=True)
        payload = [page.model_dump() for page in pages]
        _write_atomic(
            self._page_file(document_id),
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        )

    def load_pages(self, document_id: str) -> list[PageText]:
        path = self._page_file(document_id)
        if not path.exists():
            raise DocumentNotFoundError(document_id)
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [PageText.model_validate(item) for item in raw]

    def get_page(self, document_id: str, page_number: int) -> PageText | None:
        for page in self.load_pages(document_id):
            if page.page_number == page_number:
                return page
        return None

    def delete_pages(self, document_id: str) -> None:
        self._page_file(document_id).unlink(missing_ok=True)

    # Figures
    @property
    def figures_dir(self) -> Path:
        return self._index_path / "figures"

    def save_figures(self, document_id: str, figures: list[FigureRecord]) -> None:
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        payload = [figure.model_dump() for figure in figures]
        _write_atomic(
            self._figure_file(document_id),
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        )

    def load_figures(self, document_id: str) -> list[FigureRecord]:
        path = self._figure_file(document_id)
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [FigureRecord.model_validate(item) for item in raw]

    def figures_for_page(self, document_id: str, page_number: int) -> list[FigureRecord]:
        return [
            figure
            for figure in self.load_figures(document_id)
            if figure.page_number == page_number
        ]

    def delete_figures(self, document_id: str) -> None:
        self._figure_file(document_id).unlink(missing_ok=True)
        directory = self.figures_dir / self._safe_id(document_id)
        if directory.is_dir():
            for image in directory.glob("*.png"):
                image.unlink(missing_ok=True)
            directory.rmdir()

    def resolve_figure_path(self, document_id: str, figure_id: str) -> Path:
        """Resolve a registered figure without allowing directory escape."""
        for figure in self.load_figures(document_id):
            if figure.figure_id == figure_id:
                root = self.figures_dir.resolve()
                candidate = (root / figure.stored_file).resolve()
                if not candidate.is_relative_to(root) or not candidate.is_file():
                    raise DocumentNotFoundError(figure_id)
                return candidate
        raise DocumentNotFoundError(figure_id)

    def pending_files(self) -> list[str]:
        """List approved source files not yet indexed, comparing filenames."""
        from app.ingestion.standalone_images import is_image_document

        if not self._corpus_path.is_dir():
            return []
        indexed = {record.filename for record in self.load().values()}
        return sorted(
            path.name
            for path in self._corpus_path.iterdir()
            if path.is_file()
            and (path.suffix.lower() == ".pdf" or is_image_document(path))
            and path.name not in indexed
        )

    # Source files
    def resolve_source_path(self, document_id: str) -> Path:
        """Resolve a registered source without allowing directory escape."""
        record = self.get(document_id)
        corpus_root = self._corpus_path.resolve()
        candidate = (corpus_root / record.filename).resolve()
        if not candidate.is_relative_to(corpus_root):
            raise DocumentNotFoundError(document_id)
        if not candidate.is_file():
            raise DocumentNotFoundError(document_id)
        return candidate

    def _page_file(self, document_id: str) -> Path:
        return self._pages_dir / f"{self._safe_id(document_id)}.json"

    def _figure_file(self, document_id: str) -> Path:
        return self.figures_dir / f"{self._safe_id(document_id)}.json"

    @staticmethod
    def _safe_id(document_id: str) -> str:
        safe = "".join(c for c in document_id if c.isalnum() or c in "-_")
        if not safe or safe != document_id:
            raise DocumentNotFoundError(document_id)
        return safe
