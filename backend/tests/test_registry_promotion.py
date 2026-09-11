from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.corpus.registry import CorpusRegistry
from app.schemas.chunks import PageText
from app.schemas.figures import FigureRecord


class RegistryPromotionTests(unittest.TestCase):
    def test_restores_previous_artifacts_when_storage_fails(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            registry = CorpusRegistry(base / "index", base / "corpus")
            old_page = PageText(
                page_number=1,
                text="old",
                char_count=3,
                is_empty=False,
                needs_ocr_review=False,
            )
            registry.save_pages("document", [old_page])
            registry.save_figures("document", [])
            old_image = registry.figures_dir / "document" / "p1-f01.png"
            old_image.parent.mkdir(parents=True)
            old_image.write_bytes(b"old")

            stage = base / "stage" / "figures"
            new_image = stage / "document" / "p1-f01.png"
            new_image.parent.mkdir(parents=True)
            new_image.write_bytes(b"new")
            new_page = old_page.model_copy(update={"text": "new", "char_count": 3})
            figure = FigureRecord(
                figure_id="document-p1-f01",
                document_id="document",
                page_number=1,
                stored_file="document/p1-f01.png",
                width=100,
                height=100,
                content_hash="hash",
            )

            with self.assertRaises(RuntimeError):
                with registry.promote_document_artifacts(
                    "document", [new_page], [figure], stage
                ):
                    raise RuntimeError("vector replacement failed")

            self.assertEqual(registry.load_pages("document"), [old_page])
            self.assertEqual(registry.load_figures("document"), [])
            self.assertEqual(old_image.read_bytes(), b"old")


if __name__ == "__main__":
    unittest.main()
