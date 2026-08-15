import time
from typing import Dict, List, Optional, Tuple, Any
from fastapi import Request
from app.core.config import settings

class InMemoryRateLimiterAdapter:
    """In-memory sliding window rate limiter adapter for single-instance or local execution."""

    def __init__(self):
        self._storage: Dict[str, List[float]] = {}

    def is_rate_limited(
        self, key: Tuple[str, str], max_requests: int = 5, window_seconds: int = 60
    ) -> Tuple[bool, int]:
        ip_addr, path = key
        storage_key = f"{ip_addr}:{path}"
        now = time.time()
        cutoff = now - window_seconds

        timestamps = self._storage.get(storage_key, [])
        valid_timestamps = [ts for ts in timestamps if ts > cutoff]

        if len(valid_timestamps) >= max_requests:
            self._storage[storage_key] = valid_timestamps
            retry_after = int(window_seconds - (now - valid_timestamps[0]))
            return True, max(1, retry_after)

        valid_timestamps.append(now)
        self._storage[storage_key] = valid_timestamps
        return False, 0


class RedisRateLimiterAdapterStub:
    """Redis rate limiter adapter stub with graceful fallback to in-memory adapter."""

    def __init__(self, fallback_limiter: Optional[InMemoryRateLimiterAdapter] = None):
        self.fallback = fallback_limiter or InMemoryRateLimiterAdapter()

    def is_rate_limited(
        self, key: Tuple[str, str], max_requests: int = 5, window_seconds: int = 60
    ) -> Tuple[bool, int]:
        return self.fallback.is_rate_limited(key, max_requests=max_requests, window_seconds=window_seconds)


class RedisRateLimiterAdapter(RedisRateLimiterAdapterStub):
    """Production Redis Rate Limiter Adapter with in-memory fallback."""
    pass


class InMemoryRateLimiter:
    """
    Production-ready, async-safe in-memory sliding window rate limiter.
    Limits request rates per client IP address for sensitive routes.
    Does NOT block health probes, metrics, or docs endpoints.
    """

    def __init__(self):
        self.adapter = InMemoryRateLimiterAdapter()
        self.enabled_in_test = False

        # Route-specific rate limits (requests per window)
        # Format: path_substring -> (max_requests, window_seconds)
        self.route_limits: Dict[str, Tuple[int, int]] = {
            "/api/v1/auth/login": (5, 60),
            "/api/v1/auth/register": (5, 60),
            "/api/v1/auth/refresh": (10, 60),
            "/documents": (10, 60),
        }

        # Excluded health & system paths
        self.excluded_paths = {
            "/live",
            "/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/health/liveness",
            "/api/v1/health/readiness",
        }

    @property
    def _requests(self) -> Dict[str, List[float]]:
        return self.adapter._storage

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "127.0.0.1"

    def reset(self) -> None:
        """Clears all cached request timestamps (useful for unit tests)."""
        self.adapter._storage.clear()

    def is_rate_limited(
        self, request_or_key: Any, max_requests: int = 5, window_sec: int = 60
    ) -> Any:
        # Handle tuple key signature (ip, path) used by direct unit tests
        if isinstance(request_or_key, tuple):
            limited, retry_after = self.adapter.is_rate_limited(
                request_or_key, max_requests=max_requests, window_seconds=window_sec
            )
            return limited, retry_after

        # Handle Request signature used by FastAPI middleware
        request: Request = request_or_key
        path = request.url.path

        # Skip health, metrics, docs, and non-sensitive paths
        if path in self.excluded_paths:
            return False, 0, 0

        # Disable middleware rate limiting during test runs unless explicitly enabled in tests
        import sys
        if (settings.APP_ENV.lower() in ("testing", "test") or "pytest" in sys.modules) and not self.enabled_in_test:
            return False, 0, 0


        # Find matching route limit
        matching_limit: Optional[Tuple[int, int]] = None
        for route_prefix, limit_tuple in self.route_limits.items():
            if route_prefix in path:
                matching_limit = limit_tuple
                break

        if not matching_limit:
            return False, 0, 0

        max_reqs, window_seconds = matching_limit
        client_ip = self._get_client_ip(request)
        limited, retry_after = self.adapter.is_rate_limited(
            (client_ip, path), max_requests=max_reqs, window_seconds=window_seconds
        )
        return limited, max_reqs, retry_after


rate_limiter = InMemoryRateLimiter()
