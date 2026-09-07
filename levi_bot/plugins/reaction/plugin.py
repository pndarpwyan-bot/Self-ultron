from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, ReactionTypeEmoji
from database.db import Database

router = Router(name="reaction")

@router.message(Command("reaction"))
async def reaction(message: Message, db: Database) -> None:
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 2 or parts[1] not in {"on", "off"}:
        await message.answer("/reaction on ❤️ یا /reaction off"); return
    emoji = parts[2][:8] if len(parts) == 3 else "❤"
    await db.execute("""INSERT INTO reactions(chat_id,emoji,enabled) VALUES(?,?,?)
      ON CONFLICT(chat_id) DO UPDATE SET emoji=excluded.emoji,enabled=excluded.enabled""",
      (message.chat.id, emoji, int(parts[1] == "on")))
    if parts[1] == "on":
        try: await message.react([ReactionTypeEmoji(emoji=emoji)])
        except Exception: await message.answer("تنظیم ذخیره شد؛ این Emoji/Chat ممکن است Reaction ربات را نپذیرد."); return
    await message.answer("تنظیم ری‌اکشن ذخیره شد.")
