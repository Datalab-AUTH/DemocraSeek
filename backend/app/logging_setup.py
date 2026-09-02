"""Structured JSON logging with sensitive fields removed."""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from typing import Any

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

# Standard LogRecord fields.
_STANDARD = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module",
    "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs",
    "relativeCreated", "thread", "threadName", "processName", "process", "taskName",
    "message", "asctime",
}

# Fields excluded from every log entry.
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
