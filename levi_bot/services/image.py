"""Safe Pillow image inspection and resizing."""
from __future__ import annotations

import asyncio
from io import BytesIO
from PIL import Image


async def image_info(data: bytes) -> dict[str, object]:
    def inspect() -> dict[str, object]:
        with Image.open(BytesIO(data)) as image:
            return {"format": image.format, "width": image.width, "height": image.height,
                    "mode": image.mode, "animated": bool(getattr(image, "is_animated", False))}
    return await asyncio.to_thread(inspect)


async def resize_image(data: bytes, width: int, height: int) -> BytesIO:
    if not (1 <= width <= 4096 and 1 <= height <= 4096):
        raise ValueError("ابعاد باید بین ۱ و ۴۰۹۶ باشند.")
    def resize() -> BytesIO:
        with Image.open(BytesIO(data)) as image:
            image.thumbnail((width, height), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.convert("RGB").save(output, "JPEG", quality=90, optimize=True)
            output.seek(0)
            return output
    return await asyncio.to_thread(resize)
