"""Validated values crossing the language-provider boundary."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LanguageRoute(BaseModel):
    """Detected source language and a meaning-preserving English rendering."""

    model_config = ConfigDict(frozen=True)

    language_code: str = Field(pattern=r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
    language_name: str = Field(min_length=1, max_length=80)
    english_text: str = Field(min_length=1)
