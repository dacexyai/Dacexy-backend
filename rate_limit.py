from __future__ import annotations
import time
import logging
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.shared.config.settings import settings

log = logging.getLogger("ratelimit")

# Simple in-memory rate limiter (per IP)
_counters: dict = defaultdict(lambda: {"count": 0, "reset_at": 0})


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Pick limit based on path
        if "/auth/" in path:
            limit = settings.RATE_LIMIT_AUTH_RPM
        elif "/ai/" in path:
            limit = settings.RATE_LIMIT_AI_RPM
        else:
            limit = settings.RATE_LIMIT_DEFAULT_RPM

        now = time.time()
        bucket = _counters[f"{ip}:{path}"]

        if now > bucket["reset_at"]:
            bucket["count"] = 0
            bucket["reset_at"] = now + 60

        bucket["count"] += 1

        if bucket["count"] > limit:
            return Response(
                content='{"detail":"Rate limit exceeded. Try again later."}',
                status_code=429,
                media_type="application/json",
            )

        return await call_next(request)
