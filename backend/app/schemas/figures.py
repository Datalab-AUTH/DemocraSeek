"""Stored and API-facing figure schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FigureRecord(BaseModel):
    """One extracted figure, as stored by the ingestion pipeline."""

    model_config = ConfigDict(frozen=True)

    figure_id: str
    document_id: str
    page_number: int = Field(ge=1)
    # Path relative to the figures directory.
    stored_file: str
    # Extracted caption, or empty.
    caption: str = ""
    width: int
    height: int
    # Image hash used to remove repeated decoration.
    content_hash: str


class Figure(BaseModel):
    """A figure as returned by the API, alongside the citation that surfaced it."""

    figure_id: str
    document_id: str
    document_title: str
    page_number: int
    caption: str = ""
    width: int
    height: int
    image_url: str
    source_url: str
