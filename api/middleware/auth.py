"""
auth.py
API key authentication middleware.
Validates the X-API-Key header before a request reaches a route.

Keys are stored as SHA-256 hashes — never plain text.
"""

import os
import hashlib
import hmac
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Rejects requests without a valid X-API-Key header.
    Skips /health so uptime probes are not blocked.
    """

    API_KEYS_ENV = "API_KEYS"        # comma-separated list of keys (dev)
    API_KEY_SECRET_ENV = "API_KEY_SECRET"

    def __init__(self, app):
        """
        TODO:
          super().__init__(app)
          self.api_key_hash = hashlib.sha256(
              os.getenv(API_KEY_SECRET_ENV, "change-me").encode()).hexdigest()
        """
        
        super().__init__(app)

        self.api_key_hash = hashlib.sha256(
            os.getenv(self.API_KEY_SECRET_ENV, "change-me").encode()
        ).hexdigest()

    async def dispatch(self, request: Request, call_next):
        """
        Validate the API key for each incoming request.

        TODO:
          1. Permit if request.url.path.startswith("/health")
          2. Read "X-API-Key" header
          3. Compare sha256(header_value) with stored hash using hmac.compare_digest
          4. On mismatch: return JSONResponse 401 "Invalid API key"
          5. Otherwise: call_next(request)
        """
        
        if request.url.path.startswith("/health"):
          return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
          return JSONResponse(
              status_code=401,
              content={"detail": "Missing X-API-Key header"}
          )

        if not hmac.compare_digest(hashlib.sha256(api_key.encode()).hexdigest(), self.api_key_hash):
          return JSONResponse(
              status_code=401,
              content={"detail": "Invalid API key"}
          )

        return await call_next(request)