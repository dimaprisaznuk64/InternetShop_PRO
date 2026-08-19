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
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        if not getattr(request.app, "debug", False):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter.

    Limits:
      - login/register: 10 requests per minute per IP
      - other endpoints: 100 requests per minute per IP

    Disabled when app.debug is True (test/dev mode).
    """

    def __init__(self, app, login_limit: int = 10, default_limit: int = 100):
        super().__init__(app)
        self._login_limit = login_limit
        self._default_limit = default_limit
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _is_rate_limited(self, key: str, limit: int, window: int = 60) -> bool:
        now = time.time()
        cutoff = now - window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        if len(self._requests[key]) >= limit:
            return True
        self._requests[key].append(now)
        return False

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting in debug/test mode
        if getattr(request.app, "debug", False):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Auth endpoints: stricter limit
        if path in ("/api/auth/login", "/api/auth/register", "/api/auth/token"):
            key = f"auth:{client_ip}"
            limit = self._login_limit
        else:
            key = f"api:{client_ip}"
            limit = self._default_limit

        if self._is_rate_limited(key, limit):
            logger.warning("Rate limit exceeded for %s on %s", client_ip, path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
            )

        return await call_next(request)

    def reset(self):
        """Reset all counters (for testing)."""
        self._requests.clear()
