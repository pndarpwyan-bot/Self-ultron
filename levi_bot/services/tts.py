"""Async text-to-speech backed by gTTS."""
from __future__ import annotations

import asyncio
from io import BytesIO
from gtts import gTTS


async def text_to_speech(text: str, language: str = "fa") -> BytesIO:
    if not text.strip() or len(text) > 2000:
        raise ValueError("متن باید بین ۱ تا ۲۰۰۰ نویسه باشد.")
    def generate() -> BytesIO:
        output = BytesIO()
        gTTS(text=text, lang=language).write_to_fp(output)
        output.seek(0)
        return output
    return await asyncio.to_thread(generate)
