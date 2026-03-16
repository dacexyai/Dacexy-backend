from __future__ import annotations
import json
import logging
from typing import Optional
import httpx
from src.shared.config.settings import settings

log = logging.getLogger("cache")


class UpstashRedis:
    def __init__(self):
        self.url = settings.UPSTASH_REDIS_REST_URL
        self.token = settings.UPSTASH_REDIS_REST_TOKEN

    @property
    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    async def get(self, key: str) -> Optional[str]:
        if not self.url:
            return None
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"{self.url}/get/{key}", headers=self._headers, timeout=5)
                data = r.json()
                return data.get("result")
        except Exception as e:
            log.warning("Redis get error: %s", e)
            return None

    async def set(self, key: str, value: str, ex: int = 3600) -> bool:
        if not self.url:
            return False
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"{self.url}/set/{key}/{value}/ex/{ex}", headers=self._headers, timeout=5)
                return r.json().get("result") == "OK"
        except Exception as e:
            log.warning("Redis set error: %s", e)
            return False

    async def delete(self, key: str) -> bool:
        if not self.url:
            return False
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"{self.url}/del/{key}", headers=self._headers, timeout=5)
                return True
        except Exception:
            return False

    async def ping(self) -> bool:
        if not self.url:
            return False
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"{self.url}/ping", headers=self._headers, timeout=5)
                return r.json().get("result") == "PONG"
        except Exception:
            return False


_redis: UpstashRedis | None = None


def get_redis() -> UpstashRedis:
    global _redis
    if _redis is None:
        _redis = UpstashRedis()
    return _redis
