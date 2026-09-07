"""Fiat exchange rates with cache and timeout."""
from __future__ import annotations

import time
import aiohttp


class CurrencyService:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.cache: dict[tuple[str, str], tuple[float, float]] = {}

    async def convert(self, source: str, target: str, amount: float = 1.0) -> float:
        source, target = source.upper(), target.upper()
        if not (source.isalpha() and target.isalpha() and len(source) == len(target) == 3):
            raise ValueError("کد ارز باید سه‌حرفی باشد.")
        if amount <= 0 or amount > 1_000_000_000:
            raise ValueError("مبلغ نامعتبر است.")
        key = (source, target)
        cached = self.cache.get(key)
        if cached and cached[0] > time.monotonic():
            return amount * cached[1]
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(f"{self.base_url}/latest", params={"from": source, "to": target}) as response:
                data = await response.json(content_type=None)
                if response.status >= 400 or target not in data.get("rates", {}):
                    raise RuntimeError("نرخ ارز دریافت نشد.")
                rate = float(data["rates"][target])
        self.cache[key] = (time.monotonic() + 600, rate)
        return amount * rate
