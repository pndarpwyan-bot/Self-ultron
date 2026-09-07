"""Start, health and statistics handlers."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.db import Database

router = Router(name="start")

MENU = [
    ("⚙️ تنظیمات", "menu:settings"), ("👤 پروفایل", "menu:profile"),
    ("🤖 پاسخ خودکار", "menu:autoreply"), ("🛡️ فیلتر", "menu:filter"),
    ("❤️ ری‌اکشن", "menu:reaction"), ("📨 فوروارد", "menu:forward"),
    ("⏰ زمان‌بندی", "menu:scheduler"), ("📦 محتوا", "menu:content"),
    ("👥 مدیریت گروه", "menu:groups"), ("🔤 فونت", "menu:fonts"),
    ("🌐 ترجمه", "menu:translate"), ("🧠 هوش مصنوعی", "menu:ai"),
    ("🎙️ صدا", "menu:voice"), ("🖼️ تصویر", "menu:image"),
    ("💰 ارز", "menu:currency"), ("🧮 ابزارها", "menu:tools"),
    ("🎮 بازی‌ها", "menu:games"), ("🐱 بازی میویی", "menu:meow"),
    ("📊 آمار", "menu:stats"), ("ℹ️ راهنما", "menu:help"),
]


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=a[0], callback_data=a[1]), InlineKeyboardButton(text=b[0], callback_data=b[1])]
        for a, b in zip(MENU[::2], MENU[1::2])
    ])


@router.message(CommandStart())
async def start_handler(message: Message, db: Database) -> None:
    await db.increment_stat("commands")
    await message.answer(
        f"سلام <b>{message.from_user.full_name}</b>!\n"
        "به دستیار چندمنظوره Levi خوش آمدید. یک بخش را انتخاب کنید:",
        reply_markup=main_keyboard(),
    )


@router.message(Command("ping"))
async def ping(message: Message) -> None:
    await message.answer("Pong! ربات پاسخ‌گو است.")


@router.message(Command("alive"))
async def alive(message: Message) -> None:
    await message.answer("✅ سرویس فعال است و Polling ادامه دارد.")


@router.message(Command("stats"))
async def stats(message: Message, db: Database) -> None:
    users = await db.fetchone("SELECT COUNT(*) AS n FROM users")
    groups = await db.fetchone("SELECT COUNT(*) AS n FROM chats WHERE chat_type IN ('group','supergroup')")
    updates = await db.fetchone("SELECT value FROM statistics WHERE key='updates'")
    errors = await db.fetchone("SELECT value FROM statistics WHERE key='errors'")
    await message.answer(
        "<b>📊 آمار ربات</b>\n"
        f"کاربران: {users['n']}\nگروه‌ها: {groups['n']}\n"
        f"پیام/رویداد: {updates['value'] if updates else 0}\nخطاها: {errors['value'] if errors else 0}"
    )
