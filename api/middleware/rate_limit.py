"""
rate_limit.py
Per-API-key request rate limiter.
Built on slowapi — limits requests per minute per key.

Policy: 100 requests / minute / key.
"""

import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from limits import parse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Limits request rate per client IP / API key using slowapi.
    Exceeds are answered with 429 Too Many Requests.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        """
        TODO:
          super().__init__(app)
          self.limiter = Limiter(
              key_func=get_remote_address,
              default_limits=[f"{max_requests}/{window_seconds}minute"]
          )
          app.state.limiter = self.limiter
        """
        
        super().__init__(app)

        self.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[f"{max_requests}/{window_seconds}minute"]
        )
        # NOTE: no app.state here — a middleware's `app` arg is the NEXT
        # app down the stack (e.g. CORSMiddleware), not the FastAPI app,
        # so it has no .state. The limiter lives on self; dispatch uses
        # self.limiter.limiter (the underlying `limits` engine) directly.

        # Limiter itself exposes no .hit() — enforcement goes through its
        # underlying `limits` engine: hit(parsed_limit, key) -> bool.
        # Parsed once here so a bad limit string fails at startup, not per request.
        limit_str = (
            f"{max_requests}/minute"
            if window_seconds == 60
            else f"{max_requests} per {window_seconds} seconds"
        )
        self._parsed_limit = parse(limit_str)

    async def dispatch(self, request: Request, call_next):
        """
        Enforce the limit for each incoming request.

        TODO:
          1. Skip /health (uptime probes should never be throttled)
          2. Resolve key: prefer X-API-Key header, else client IP
          3. Check limiter window; if exceeded return 429 JSONResponse
          4. Otherwise: call_next(request)
        """
        
        if request.url.path.startswith("/health"):
          return await call_next(request)

        limit_key = request.headers.get("X-API-Key")

        if not limit_key:
          limit_key = get_remote_address(request)

        if not self.limiter.limiter.hit(self._parsed_limit, limit_key):
          return JSONResponse(
              status_code=429,
              content={"detail": "Too many requests. Please try again later."}
          )

        return await call_next(request)