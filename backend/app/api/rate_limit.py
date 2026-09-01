"""Basic in-memory sliding-window rate limiting.

Adequate for a single-instance prototype and honest about it: with more than
one worker process the limit applies per process. A shared limiter would need
Redis or a gateway, which is a deployment decision that has not been made.
See docs/D5.5-technical-documentation.md, "Known limitations".
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, *, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max_requests
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> bool:
        """Record a hit. Returns False when the caller is over the limit."""
        now = time.monotonic()
        with self._lock:
            bucket = self._hits[key]
            cutoff = now - self._window
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self._max_requests:
                return False
            bucket.append(now)
            return True

    def retry_after(self, key: str) -> int:
        with self._lock:
            bucket = self._hits.get(key)
            if not bucket:
                return 0
            return max(1, int(self._window - (time.monotonic() - bucket[0])))
