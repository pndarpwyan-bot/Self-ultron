"""Replaceable OpenAI-compatible chat provider."""
from __future__ import annotations

import asyncio
import aiohttp


class AIServiceError(RuntimeError):
    pass


class AIService:
    def __init__(self, api_key: str | None, base_url: str, model: str, timeout: float = 35) -> None:
        self.api_key, self.base_url, self.model, self.timeout = api_key, base_url.rstrip("/"), model, timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def ask(self, prompt: str, system: str = "You are a concise helpful assistant.") -> str:
        if not self.api_key:
            raise AIServiceError("کلید AI_API_KEY تنظیم نشده است.")
        if not prompt.strip() or len(prompt) > 12000:
            raise AIServiceError("متن باید بین ۱ تا ۱۲۰۰۰ نویسه باشد.")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": [{"role": "system", "content": system},
                   {"role": "user", "content": prompt}], "temperature": 0.4, "max_tokens": 1200}
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.base_url}/chat/completions", headers=headers, json=payload) as response:
                    data = await response.json(content_type=None)
                    if response.status >= 400:
                        raise AIServiceError(str(data.get("error", {}).get("message", "خطای سرویس AI")))
                    return str(data["choices"][0]["message"]["content"]).strip()
        except asyncio.TimeoutError as exc:
            raise AIServiceError("زمان پاسخ سرویس AI تمام شد.") from exc
        except aiohttp.ClientError as exc:
            raise AIServiceError("اتصال به سرویس AI برقرار نشد.") from exc
