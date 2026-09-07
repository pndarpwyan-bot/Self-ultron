"""Small in-memory async rate limiter."""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, limit: int = 8, window: float = 10.0) -> None:
        self.limit = limit
        self.window = window
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> bool:
        now = time.monotonic()
        async with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= now - self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True

    async def cleanup(self) -> None:
        now = time.monotonic()
        async with self._lock:
            stale = [key for key, hits in self._hits.items() if not hits or hits[-1] < now - self.window]
            for key in stale:
                self._hits.pop(key, None)
