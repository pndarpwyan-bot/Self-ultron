"""Owner/admin management panel."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import Settings
from database.db import Database

router = Router(name="admin")


def args(message: Message) -> list[str]:
    return (message.text or "").split()[1:]


async def is_admin(user_id: int, db: Database, settings: Settings) -> bool:
    if settings.admin_id == user_id:
        return True
    return bool(await db.fetchone("SELECT 1 FROM admins WHERE user_id=?", (user_id,)))


@router.message(Command("admin"))
async def admin_panel(message: Message, db: Database, settings: Settings) -> None:
    if not await is_admin(message.from_user.id, db, settings):
        await message.answer("دسترسی ندارید.")
        return
    users = await db.fetchone("SELECT COUNT(*) n FROM users")
    blocked = await db.fetchone("SELECT COUNT(*) n FROM users WHERE is_blocked=1")
    await message.answer(f"<b>پنل مدیر</b>\nکاربران: {users['n']}\nمسدود: {blocked['n']}\n/adminhelp")


@router.message(Command("adminhelp"))
async def admin_help(message: Message, db: Database, settings: Settings) -> None:
    if await is_admin(message.from_user.id, db, settings):
        await message.answer("/block USER_ID\n/unblock USER_ID\n/allow USER_ID\n/disallow USER_ID\n/addadmin USER_ID\n/deladmin USER_ID")


async def change_user_flag(message: Message, db: Database, settings: Settings, column: str, value: int) -> None:
    if not await is_admin(message.from_user.id, db, settings):
        return
    values = args(message)
    if not values or not values[0].lstrip("-").isdigit():
        await message.answer("شناسه عددی کاربر لازم است.")
        return
    user_id = int(values[0])
    await db.execute("INSERT OR IGNORE INTO users(user_id,full_name) VALUES(?,?)", (user_id, str(user_id)))
    if column not in {"is_blocked", "is_allowed"}:
        raise ValueError("Invalid user flag")
    await db.execute(f"UPDATE users SET {column}=? WHERE user_id=?", (value, user_id))
    await message.answer("انجام شد.")


@router.message(Command("block"))
async def block(message: Message, db: Database, settings: Settings) -> None:
    await change_user_flag(message, db, settings, "is_blocked", 1)


@router.message(Command("unblock"))
async def unblock(message: Message, db: Database, settings: Settings) -> None:
    await change_user_flag(message, db, settings, "is_blocked", 0)


@router.message(Command("allow"))
async def allow(message: Message, db: Database, settings: Settings) -> None:
    await change_user_flag(message, db, settings, "is_allowed", 1)


@router.message(Command("disallow"))
async def disallow(message: Message, db: Database, settings: Settings) -> None:
    await change_user_flag(message, db, settings, "is_allowed", 0)


@router.message(Command("addadmin", "deladmin"))
async def admin_change(message: Message, db: Database, settings: Settings) -> None:
    if settings.admin_id != message.from_user.id:
        return
    values = args(message)
    if not values or not values[0].isdigit():
        await message.answer("شناسه عددی لازم است.")
        return
    if message.text.startswith("/addadmin"):
        await db.execute("INSERT OR IGNORE INTO admins(user_id) VALUES(?)", (int(values[0]),))
    else:
        await db.execute("DELETE FROM admins WHERE user_id=?", (int(values[0]),))
    await message.answer("انجام شد.")
