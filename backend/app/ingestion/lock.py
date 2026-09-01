"""Prevent concurrent ingestion and recover stale writer locks."""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

LOCK_FILENAME = "ingestion.lock"
# Maximum lock age before takeover.
STALE_AFTER_SECONDS = 6 * 60 * 60


class IngestionInProgressError(RuntimeError):
    """Another ingestion process holds the lock."""


@contextmanager
def ingestion_lock(index_path: Path) -> Iterator[None]:
    """Hold the ingestion lock for the duration of the block."""
    index_path.mkdir(parents=True, exist_ok=True)
    lock_file = index_path / LOCK_FILENAME

    if not _acquire(lock_file):
        held = _read(lock_file)
        age = time.time() - held.started_at
        if age < STALE_AFTER_SECONDS:
            raise IngestionInProgressError(
                f"Another ingestion is already running (pid {held.pid}, started "
                f"{int(age)}s ago). Wait for it to finish, or remove {lock_file} "
                f"if you are certain that process is gone."
            )
        logger.warning(
            "stale_ingestion_lock_taken_over",
            extra={"previous_pid": held.pid, "age_seconds": int(age)},
        )
        lock_file.unlink(missing_ok=True)
        if not _acquire(lock_file):  # pragma: no cover - lost a race for a stale lock
            raise IngestionInProgressError(
                f"Could not take over the stale lock at {lock_file}."
            )

    try:
        yield
    finally:
        lock_file.unlink(missing_ok=True)


def _acquire(lock_file: Path) -> bool:
    try:
        handle = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid(), "started_at": time.time()}, stream)
    return True


@dataclass(frozen=True)
class LockHolder:
    """Lock owner; invalid lock data is treated as stale."""

    pid: int = 0
    started_at: float = 0.0


def _read(lock_file: Path) -> LockHolder:
    try:
        content = json.loads(lock_file.read_text(encoding="utf-8"))
        return LockHolder(pid=int(content["pid"]), started_at=float(content["started_at"]))
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return LockHolder()
