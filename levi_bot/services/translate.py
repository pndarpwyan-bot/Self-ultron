"""Translation provider with bounded TTL cache."""
from __future__ import annotations

import asyncio
import hashlib
import time
from collections import OrderedDict

import aiohttp


class TranslationService:
    def __init__(self, url: str, api_key: str | None = None) -> None:
        self.url, self.api_key = url, api_key
        self.cache: OrderedDict[str, tuple[float, str]] = OrderedDict()

    async def translate(self, text: str, target: str, source: str = "auto") -> str:
        if not text.strip() or len(text) > 4000 or not target.isalpha() or len(target) > 5:
            raise ValueError("متن یا کد زبان نامعتبر است.")
        key = hashlib.sha256(f"{source}:{target}:{text}".encode()).hexdigest()
        cached = self.cache.get(key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        params = {"q": text, "langpair": f"{source}|{target}"}
        if self.api_key:
            params["key"] = self.api_key
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.get(self.url, params=params) as response:
                    data = await response.json(content_type=None)
                    if response.status >= 400:
                        raise RuntimeError("خطای سرویس ترجمه")
                    result = data.get("responseData", {}).get("translatedText") or data.get("translatedText")
                    if not result:
                        raise RuntimeError("پاسخ ترجمه معتبر نبود")
        except asyncio.TimeoutError as exc:
            raise RuntimeError("زمان ترجمه تمام شد") from exc
        self.cache[key] = (time.monotonic() + 1800, str(result))
        while len(self.cache) > 256:
            self.cache.popitem(last=False)
        return str(result)
