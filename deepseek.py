from __future__ import annotations
import json
from typing import AsyncIterator
import httpx
from src.shared.config.settings import settings


class DeepSeekProvider:
    BASE_URL = "https://api.deepseek.com/v1"

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
            timeout=settings.DEEPSEEK_TIMEOUT,
        )

    async def chat(self, messages: list[dict], model: str = "deepseek-chat", stream: bool = False):
        payload = {"model": model, "messages": messages, "stream": stream}
        if stream:
            return self._stream(payload)
        r = await self.client.post("/chat/completions", json=payload)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    async def _stream(self, payload: dict) -> AsyncIterator[str]:
        async with self.client.stream("POST", "/chat/completions", json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except Exception:
                        pass

    async def aclose(self):
        await self.client.aclose()
