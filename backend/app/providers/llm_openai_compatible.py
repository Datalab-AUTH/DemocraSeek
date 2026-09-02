"""LLM adapter for OpenAI-compatible chat-completions endpoints."""

from __future__ import annotations

import json
import logging

import httpx

from app.providers.base import ProviderError

logger = logging.getLogger(__name__)


class OpenAICompatibleLLM:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
        timeout_seconds: float,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
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
            raise ProviderError("LLM_BASE_URL is empty.")
        if not self._api_key:
            raise ProviderError("LLM_API_KEY is empty.")
        if not self._model:
            raise ProviderError("LLM_MODEL is empty.")

    def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self._model,
            "temperature": self._temperature,
            "max_tokens": self._max_output_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            response = self._client.post(f"{self._base_url}/chat/completions", json=payload)
        except httpx.HTTPError as exc:
            raise ProviderError(f"LLM request failed: {type(exc).__name__}") from exc

        if response.status_code >= 400:
            # Body may echo back prompt content; log status only.
            logger.error(
                "llm_http_error", extra={"status_code": response.status_code, "model": self._model}
            )
            raise ProviderError(f"LLM endpoint returned HTTP {response.status_code}.")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError("LLM response had an unexpected shape.") from exc

        if not isinstance(content, str):
            raise ProviderError("LLM response content was not a string.")
        return content

    def close(self) -> None:
        self._client.close()
