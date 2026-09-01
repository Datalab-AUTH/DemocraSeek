"""Structured JSON logging.

What is logged: request ids, policy codes, policy version, provider and model
names, document ids, timings and error categories.

What is never logged: API keys, connection strings, system prompts, compiled
policy text, retrieved passages, or user questions and answers. Those would
turn an operational log into a copy of the corpus and of the conversation.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from typing import Any

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

#: Attributes present on every LogRecord; anything else is treated as a field.
_STANDARD = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module",
    "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs",
    "relativeCreated", "thread", "threadName", "processName", "process", "taskName",
    "message", "asctime",
}

#: Field names that must never appear in a log line, whatever the caller passes.
_FORBIDDEN = {
    "api_key", "llm_api_key", "embedding_api_key", "authorization",
    "password", "dsn", "vector_store_url", "llm_base_url", "embedding_base_url",
    "system_prompt", "user_prompt", "compiled_system_instructions", "question", "answer",
    "chunk_text", "evidence",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        for key, value in record.__dict__.items():
            if key in _STANDARD or key in _FORBIDDEN or key.startswith("_"):
                continue
            payload[key] = value
        if record.exc_info:
            payload["error_type"] = record.exc_info[0].__name__ if record.exc_info[0] else "Error"
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    # uvicorn's own access log would duplicate our request log.
    logging.getLogger("uvicorn.access").disabled = True
