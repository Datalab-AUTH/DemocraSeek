"""Describe images through an OpenAI-compatible endpoint during ingestion."""

from __future__ import annotations

import base64
import json
import logging

import httpx

from app.providers.base import ProviderError

logger = logging.getLogger(__name__)

# Conservative prompt because descriptions become searchable evidence.
DESCRIBE_PROMPT = """\
You are describing a figure taken from an official report so that it can be \
found later by search.

Describe ONLY what is actually visible. State the kind of figure (chart, \
diagram, photograph, map, screenshot, table image), what it shows, the labels, \
axis titles, legend entries and any numbers you can read. If the figure \
contains text, transcribe the text you can actually read.

Do not interpret, conclude, speculate or add background knowledge. If part of \
the figure is unreadable, say so instead of guessing. If the image carries no \
meaningful information (a logo, a decorative shape, a blank area), reply with \
exactly: NO_INFORMATION
"""


class OpenAICompatibleVision:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_description_chars: int,
        reasoning_effort: str = "",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._max_chars = max_description_chars
        self._reasoning_effort = reasoning_effort
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

    def validate_configuration(self) -> None:
        if not self._base_url:
            raise ProviderError("VISION_BASE_URL is empty.")
        if not self._api_key:
            raise ProviderError("VISION_API_KEY is empty.")
        if not self._model:
            raise ProviderError("VISION_MODEL is empty.")

    def describe_image(self, image_png: bytes, *, context: str = "") -> str:
        data_uri = "data:image/png;base64," + base64.b64encode(image_png).decode("ascii")
        instruction = DESCRIBE_PROMPT
        if context:
            instruction += f"\nThe document labels this figure: {context}"

        payload = {
            "model": self._model,
            "temperature": 0.0,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instruction},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
        }
        if self._reasoning_effort:
            payload["reasoning_effort"] = self._reasoning_effort
        try:
            response = self._client.post(f"{self._base_url}/chat/completions", json=payload)
        except httpx.HTTPError as exc:
            # Keep the figure even when description generation fails.
            logger.warning("vision_request_failed", extra={"error_category": type(exc).__name__})
            return ""

        if response.status_code >= 400:
            logger.warning("vision_http_error", extra={"status_code": response.status_code})
            return ""

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            logger.warning("vision_unexpected_shape")
            return ""

        if not isinstance(content, str):
            return ""
        text = " ".join(content.split())
        if not text or text.upper().startswith("NO_INFORMATION"):
            return ""
        return text[: self._max_chars]

    def close(self) -> None:
        self._client.close()
