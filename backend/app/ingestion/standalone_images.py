"""Represent a standalone image as a one-page corpus document."""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.ingestion.figures import _to_png
from app.schemas.chunks import PageText
from app.schemas.figures import FigureRecord

logger = logging.getLogger(__name__)

# Image formats supported by the bundled Pillow build.
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"})

# Distinguishes standalone images from failed PDF text extraction.
NO_TEXT_LAYER_REASON = "standalone_image_no_text_layer"


class ImageLoadError(RuntimeError):
    """The file could not be opened as an image."""


def is_image_document(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_SUFFIXES


def humanise_filename(path: Path) -> str:
    """Turn a filename into a readable, non-invented title."""
    words = re.split(r"[-_\s]+", path.stem.strip())
    cleaned = " ".join(word for word in words if word)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else path.stem


def load_image_document(
    path: Path,
    *,
    document_id: str,
    title: str,
    output_dir: Path,
) -> tuple[list[PageText], list[FigureRecord]]:
    """Load an image as one page and one figure; use its title as caption."""
    try:
        with Image.open(path) as handle:
            image = handle.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageLoadError(f"Cannot read image {path.name}: {type(exc).__name__}") from exc

    width, height = image.size
    payload = _to_png(image)

    stored_file = f"{document_id}/p1-f01.png"
    target = output_dir / stored_file
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)

    page = PageText(
        page_number=1,
        text="",
        char_count=0,
        is_empty=True,
        # Report that search depends on vision rather than a text layer.
        needs_ocr_review=True,
        ocr_reason=NO_TEXT_LAYER_REASON,
    )
    figure = FigureRecord(
        figure_id=f"{document_id}-p1-f01",
        document_id=document_id,
        page_number=1,
        stored_file=stored_file,
        caption=title,
        width=width,
        height=height,
        content_hash=hashlib.sha256(payload).hexdigest(),
    )
    logger.info(
        "image_document_loaded",
        extra={"document_id": document_id, "width": width, "height": height},
    )
    return [page], [figure]
