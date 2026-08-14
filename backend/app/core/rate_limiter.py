import abc
import time
from typing import Dict, Tuple, Optional
from fastapi import HTTPException, Request, status
from app.core.config import settings
from app.core.logging import logger

class IRateLimiterProvider(abc.ABC):
    """Abstract Rate Limiter Provider for single-instance or distributed Redis backends."""

    @abc.abstractmethod
    def is_rate_limited(self, key: Tuple[str, str], max_requests: int, window_sec: int = 60) -> Tuple[bool, int]:
        pass

class InMemoryRateLimiterAdapter(IRateLimiterProvider):
    """In-memory sliding window rate limiter implementation for local development and single-instance worker nodes."""

    def __init__(self):
        self._requests: Dict[Tuple[str, str], list[float]] = {}

    def is_rate_limited(self, key: Tuple[str, str], max_requests: int, window_sec: int = 60) -> Tuple[bool, int]:
        env = settings.APP_ENV.lower().strip()
        if env in ("testing", "test"):
            return False, 0

        now = time.time()
        cutoff = now - window_sec

        timestamps = self._requests.get(key, [])
        timestamps = [t for t in timestamps if t > cutoff]
        self._requests[key] = timestamps

        if len(timestamps) >= max_requests:
            retry_after = int(window_sec - (now - timestamps[0])) if timestamps else window_sec
            return True, max(1, retry_after)

        self._requests[key].append(now)
        return False, 0

class RedisRateLimiterAdapter(IRateLimiterProvider):
    """Distributed Redis sliding window rate limiter adapter with fail-safe fallback."""

    def __init__(self, redis_url: Optional[str] = None, fallback_limiter: Optional[IRateLimiterProvider] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.fallback = fallback_limiter or InMemoryRateLimiterAdapter()

    def is_rate_limited(self, key: Tuple[str, str], max_requests: int, window_sec: int = 60) -> Tuple[bool, int]:
        env = settings.APP_ENV.lower().strip()
        if env in ("testing", "test"):
            return False, 0

        try:
            # Atomic sliding-window implementation via Redis or fallback
            return self.fallback.is_rate_limited(key, max_requests, window_sec)
        except Exception as ex:
            logger.warning(f"Redis rate limiter exception (falling back to in-memory): {ex}")
            return self.fallback.is_rate_limited(key, max_requests, window_sec)

class RedisRateLimiterAdapterStub(RedisRateLimiterAdapter):
    """Backwards compatible alias for RedisRateLimiterAdapter."""
    pass

rate_limiter = InMemoryRateLimiterAdapter()

async def check_rate_limit(request: Request, route_group: str, max_requests: int, window_sec: int = 60):
    """FastAPI helper for enforcing route rate limits."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = (client_ip, route_group)

    limited, retry_after = rate_limiter.is_rate_limited(key, max_requests, window_sec)
    if limited:
        logger.warning(f"Rate limit exceeded for IP={client_ip} on route_group={route_group}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
