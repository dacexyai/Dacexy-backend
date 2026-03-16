from __future__ import annotations
import logging
from typing import Optional
import httpx
from src.shared.config.settings import settings

log = logging.getLogger("storage")


class SupabaseStorage:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_SERVICE_ROLE_KEY
        self.bucket = settings.SUPABASE_STORAGE_BUCKET

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.key}",
            "apikey": self.key,
        }

    async def upload(self, path: str, content: bytes, content_type: str = "application/octet-stream") -> Optional[str]:
        if not self.url or not self.key:
            return None
        try:
            async with httpx.AsyncClient() as c:
                r = await c.post(
                    f"{self.url}/storage/v1/object/{self.bucket}/{path}",
                    headers={**self._headers, "Content-Type": content_type},
                    content=content,
                    timeout=30,
                )
                if r.status_code in (200, 201):
                    return f"{self.url}/storage/v1/object/public/{self.bucket}/{path}"
                log.warning("Storage upload failed: %s", r.text)
                return None
        except Exception as e:
            log.error("Storage error: %s", e)
            return None

    async def delete(self, path: str) -> bool:
        if not self.url or not self.key:
            return False
        try:
            async with httpx.AsyncClient() as c:
                r = await c.delete(
                    f"{self.url}/storage/v1/object/{self.bucket}/{path}",
                    headers=self._headers,
                    timeout=10,
                )
                return r.status_code == 200
        except Exception:
            return False

    def public_url(self, path: str) -> str:
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{path}"
