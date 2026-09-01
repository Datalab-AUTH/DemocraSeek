"""Rerank query-chunk pairs with a local sentence-transformers model."""

from __future__ import annotations

import logging
from typing import Any

from app.providers.base import ProviderError

logger = logging.getLogger(__name__)

# Token limit; longer pairs are truncated.
MAX_SEQUENCE_LENGTH = 512


class CrossEncoderReranker:
    """Scores (question, chunk) pairs by reading them together."""

    def __init__(self, *, model: str, max_length: int = MAX_SEQUENCE_LENGTH) -> None:
        self._model_name = model
        self._max_length = max_length
        self._encoder: Any | None = None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_name(self) -> str:
        return "cross_encoder"

    def validate_configuration(self) -> None:
        """Load the model at startup so configuration failures surface early."""
        if not self._model_name:
            raise ProviderError("RERANK_MODEL is empty.")
        self._load()

    def _load(self) -> Any:
        if self._encoder is not None:
            return self._encoder
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise ProviderError(
                "RERANK_PROVIDER=cross_encoder needs sentence-transformers. "
                "Install the pinned project requirements."
            ) from exc
        # Prefer the cache, then allow one normal download attempt.
        try:
            self._encoder = CrossEncoder(
                self._model_name,
                max_length=self._max_length,
                local_files_only=True,
            )
        except Exception:
            try:
                self._encoder = CrossEncoder(
                    self._model_name,
                    max_length=self._max_length,
                    local_files_only=False,
                )
            except Exception as exc:  # model download, corrupt cache, bad name
                raise ProviderError(
                    f"Could not load rerank model {self._model_name!r}: {type(exc).__name__}"
                ) from exc
        logger.info("reranker_loaded", extra={"rerank_model": self._model_name})
        return self._encoder

    def rerank(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []
        encoder = self._load()
        try:
            scores = encoder.predict(
                [[query, document] for document in documents], show_progress_bar=False
            )
        except Exception as exc:
            raise ProviderError(f"Reranking failed: {type(exc).__name__}") from exc
        return [float(score) for score in scores]
