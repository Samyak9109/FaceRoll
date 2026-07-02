from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, request: Request) -> None:
        settings = get_settings()
        client = request.client.host if request.client else "unknown"
        now = monotonic()
        window = 60.0
        bucket = self._hits[client]
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= settings.recognition_rate_limit_per_minute:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Recognition rate limit exceeded")
        bucket.append(now)


recognition_limiter = InMemoryRateLimiter()
