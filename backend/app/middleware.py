import time
import logging
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if getattr(request.app, "debug", False):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' https://fastapi.tiangolo.com data:; "
                "connect-src 'self'"
            )
        else:
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        if not getattr(request.app, "debug", False):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# Endpoint-specific rate limits: (requests, window_seconds)
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "/api/auth/login":       (5, 60),    # 5 login attempts / min
    "/api/auth/register":    (3, 60),    # 3 registrations / min
    "/api/auth/token":       (10, 60),   # 10 token refreshes / min
    "/api/auth/logout":      (10, 60),
    "/api/profile/password": (3, 300),   # 3 password changes / 5 min
    "/api/profile":          (20, 60),   # 20 profile updates / min
}

DEFAULT_LIMIT = (100, 60)  # 100 requests / min for everything else


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter with per-endpoint limits.

    Limits:
      - login: 5/min, register: 3/min, password change: 3/5min
      - other endpoints: 100/min per IP

    Sends X-RateLimit-Remaining and X-RateLimit-Reset headers.
    """

    def __init__(self, app, force_enabled: bool = False):
        super().__init__(app)
        self._force_enabled = force_enabled
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _is_rate_limited(self, key: str, limit: int, window: int = 60) -> bool:
        now = time.time()
        cutoff = now - window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        if len(self._requests[key]) >= limit:
            return True
        self._requests[key].append(now)
        return False

    def _remaining(self, key: str, limit: int, window: int = 60) -> int:
        now = time.time()
        cutoff = now - window
        count = sum(1 for t in self._requests[key] if t > cutoff)
        return max(0, limit - count)

    def _reset_time(self, window: int = 60) -> int:
        return int(time.time()) + window

    def _get_limit(self, path: str) -> tuple[int, int]:
        # Check exact match first
        if path in RATE_LIMITS:
            return RATE_LIMITS[path]
        # Check prefix matches (e.g. /api/profile/password matches /api/profile)
        for prefix, limits in sorted(RATE_LIMITS.items(), key=lambda x: -len(x[0])):
            if path.startswith(prefix):
                return limits
        return DEFAULT_LIMIT

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting in debug/test mode unless forced
        if not self._force_enabled and getattr(request.app, "debug", False):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        limit, window = self._get_limit(path)
        key = f"rate:{path}:{client_ip}"

        if self._is_rate_limited(key, limit, window):
            logger.warning("Rate limit exceeded for %s on %s (%d/%ds)", client_ip, path, limit, window)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={
                    "Retry-After": str(window),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(self._reset_time(window)),
                },
            )

        response = await call_next(request)

        remaining = self._remaining(key, limit, window)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(self._reset_time(window))

        return response

    def reset(self):
        """Reset all counters (for testing)."""
        self._requests.clear()
