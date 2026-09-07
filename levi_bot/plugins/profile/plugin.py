from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database.db import Database

router = Router(name="profile")

@router.message(Command("profile"))
async def profile(message: Message, db: Database) -> None:
    row = await db.fetchone("SELECT * FROM users WHERE user_id=?", (message.from_user.id,))
    await message.answer(f"<b>پروفایل</b>\nشناسه: <code>{message.from_user.id}</code>\nنام: {message.from_user.full_name}\nزبان: {row['language']}\nعضویت: {row['created_at']}")

@router.message(Command("settings"))
async def settings(message: Message, db: Database) -> None:
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) == 1:
        language = await db.get_setting(message.from_user.id, "language", "fa")
        await message.answer(f"زبان فعلی: {language}\n/settings language fa|en\n/settings feature NAME on|off")
        return
    if parts[1] == "language" and len(parts) == 3 and parts[2] in {"fa", "en"}:
        await db.set_setting(message.from_user.id, "language", parts[2])
        await db.execute("UPDATE users SET language=? WHERE user_id=?", (parts[2], message.from_user.id))
        await message.answer("زبان ذخیره شد.")
    elif parts[1] == "feature" and len(parts) == 3:
        name, _, state = parts[2].partition(" ")
        if state not in {"on", "off"} or not name.replace("_", "").isalnum():
            await message.answer("نمونه: /settings feature ai on")
            return
        await db.set_setting(message.from_user.id, f"feature:{name}", state)
        await message.answer("تنظیم ذخیره شد.")
    else:
        await message.answer("تنظیم نامعتبر است.")
