import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory per-user rate limiting.

    Limits:
    - 30 requests per minute for general endpoints
    - 10 requests per minute for STT (expensive ML inference)
    - 20 requests per minute for translation (OpenAI API cost)
    """

    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(list)
        self.limits = {
            "/api/transcribe": (10, 60),
            "/api/translate": (20, 60),
            "/api/translate/stream": (20, 60),
        }
        self.default_limit = (30, 60)

    def _get_client_id(self, request: Request) -> str:
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path in ("/api/health", "/docs", "/openapi.json"):
            return await call_next(request)

        client_id = self._get_client_id(request)
        now = time.time()

        # Find matching rate limit (most-specific path first)
        limit_count, limit_window = self.default_limit
        for path, (count, window) in sorted(self.limits.items(), key=lambda x: len(x[0]), reverse=True):
            if request.url.path.startswith(path):
                limit_count, limit_window = count, window
                break

        # Clean old entries and count current window
        key = f"{client_id}:{request.url.path}"
        self.requests[key] = [t for t in self.requests[key] if now - t < limit_window]
        if not self.requests[key]:
            del self.requests[key]

        if len(self.requests[key]) >= limit_count:
            retry_after = int(limit_window - (now - self.requests[key][0]))
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Try again in {retry_after} seconds."
                },
                headers={"Retry-After": str(retry_after)},
            )

        self.requests[key].append(now)
        return await call_next(request)
