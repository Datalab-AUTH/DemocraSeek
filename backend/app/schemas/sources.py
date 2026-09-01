"""Source-inspection response models."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.chunks import DocumentType
from app.schemas.figures import Figure


class SourcePage(BaseModel):
    page_number: int
    text: str
    truncated: bool
    #: Figures printed on this page, if any.
    figures: list[Figure] = []


class SourceResponse(BaseModel):
    document_id: str
    document_title: str
    filename: str
    #: "image" documents have no text layer; their content is the picture.
    document_type: DocumentType = "pdf"
    deliverable_id: str = ""
    publication_date: str = ""
    page_count: int
    corpus_version: str
    #: Present when the request named a page.
    page: SourcePage | None = None
    #: Direct link to the original PDF, resolved server-side from the registry.
    file_url: str
