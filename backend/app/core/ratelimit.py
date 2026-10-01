"""Small in-memory rate limiter for unauthenticated endpoints.

Per process: with several API instances each enforces its own window, which is still an
effective brake on token guessing (tokens are 256-bit). Swap for Redis if you need a
global limit.
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float):
        self.limit = limit
        self.window = window_seconds
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def __call__(self, request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            key = forwarded.split(",")[0].strip()
        now = time.monotonic()
        q = self.hits[key]
        while q and q[0] <= now - self.window:
            q.popleft()
        if len(q) >= self.limit:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Too many requests. Please wait a minute.",
                headers={"Retry-After": str(int(self.window))},
            )
        q.append(now)
        if len(self.hits) > 10_000:  # keep memory bounded
            for k in [k for k, v in self.hits.items() if not v]:
                del self.hits[k]
