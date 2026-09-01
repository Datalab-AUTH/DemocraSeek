"""Embedding adapter for any OpenAI-compatible /embeddings endpoint.

Configured completely independently of the LLM adapter: different base URL,
key, model and dimensions are all supported. Changing anything here invalidates
the stored vectors and requires a controlled re-index.
"""

from __future__ import annotations

import httpx

from app.providers.base import ProviderError


class OpenAICompatibleEmbeddings:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        dimensions: int,
        batch_size: int,
        timeout_seconds: float = 60.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "openai_compatible"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def validate_configuration(self) -> None:
        if not self._base_url:
            raise ProviderError("EMBEDDING_BASE_URL is empty.")
        if not self._api_key:
            raise ProviderError("EMBEDDING_API_KEY is empty.")
        if not self._model:
            raise ProviderError("EMBEDDING_MODEL is empty.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            vectors.extend(self._embed_batch(texts[start : start + self._batch_size]))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text])[0]

    def _embed_batch(self, batch: list[str]) -> list[list[float]]:
        if not batch:
            return []
        payload: dict[str, object] = {"model": self._model, "input": batch}
        # Servers that do not support variable output size ignore this field.
        payload["dimensions"] = self._dimensions
        try:
            response = self._client.post(f"{self._base_url}/embeddings", json=payload)
        except httpx.HTTPError as exc:
            raise ProviderError(f"Embedding request failed: {type(exc).__name__}") from exc

        if response.status_code == 400 and "dimensions" in response.text:
            payload.pop("dimensions")
            response = self._client.post(f"{self._base_url}/embeddings", json=payload)

        if response.status_code >= 400:
            raise ProviderError(f"Embedding endpoint returned HTTP {response.status_code}.")

        try:
            data = response.json()["data"]
            vectors = [item["embedding"] for item in sorted(data, key=lambda d: d["index"])]
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError("Embedding response had an unexpected shape.") from exc

        for vector in vectors:
            if len(vector) != self._dimensions:
                raise ProviderError(
                    f"Embedding model {self._model!r} returned {len(vector)} dimensions but "
                    f"EMBEDDING_DIMENSIONS is {self._dimensions}. Fix the setting and re-index."
                )
        return vectors

    def close(self) -> None:
        self._client.close()
