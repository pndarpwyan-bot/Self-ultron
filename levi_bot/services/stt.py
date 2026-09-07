"""OpenAI-compatible speech-to-text provider."""
from __future__ import annotations

import aiohttp


async def speech_to_text(audio: bytes, api_key: str | None, base_url: str) -> str:
    if not api_key:
        raise RuntimeError("برای تبدیل صدا به متن، AI_API_KEY لازم است.")
    if len(audio) > 20 * 1024 * 1024:
        raise ValueError("حجم صدا بیش از ۲۰ مگابایت است.")
    form = aiohttp.FormData()
    form.add_field("file", audio, filename="voice.ogg", content_type="audio/ogg")
    form.add_field("model", "whisper-1")
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
        async with session.post(f"{base_url.rstrip('/')}/audio/transcriptions", data=form,
                                headers={"Authorization": f"Bearer {api_key}"}) as response:
            data = await response.json(content_type=None)
            if response.status >= 400:
                raise RuntimeError(data.get("error", {}).get("message", "خطای تبدیل صدا"))
            return str(data.get("text", ""))
