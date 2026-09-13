"""
rate_limit.py
Per-API-key request rate limiter.
Built on slowapi — limits requests per minute per key.

Policy: 100 requests / minute / key.
"""

import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
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
        pass

    async def dispatch(self, request: Request, call_next):
        """
        Enforce the limit for each incoming request.

        TODO:
          1. Skip /health (uptime probes should never be throttled)
          2. Resolve key: prefer X-API-Key header, else client IP
          3. Check limiter window; if exceeded return 429 JSONResponse
          4. Otherwise: call_next(request)
        """
        pass