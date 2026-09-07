"""Main panel callbacks."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from database.db import Database
from handlers.help import HELP_TEXT
from handlers.start import main_keyboard

router = Router(name="callbacks")

PAGES = {
 "settings": ("⚙️ تنظیمات", "با /settings زبان و قابلیت‌های حساب را مدیریت کنید."),
 "profile": ("👤 پروفایل", "نمایش حساب: /profile"),
 "autoreply": ("🤖 پاسخ خودکار", "/autoreply add trigger | response\n/autoreply list\n/autoreply del ID\n/autoreply toggle ID"),
 "filter": ("🛡️ فیلتر", "/filter add WORD [delete|warn|mute]\n/filter list\n/filter del ID"),
 "reaction": ("❤️ ری‌اکشن", "/reaction on ❤️ یا /reaction off؛ واکنش باید مورد پشتیبانی همان گفتگو باشد."),
 "forward": ("📨 فوروارد", "/forward add SOURCE DESTINATION\n/forward list|del ID|stop"),
 "scheduler": ("⏰ زمان‌بندی", "/schedule once ISO_TIME متن\n/schedule daily HH:MM متن\n/schedule weekly mon@HH:MM متن\n/schedule list|del|pause|resume ID"),
 "content": ("📦 محتوا", "/content save category title | text (یا Reply به رسانه)\n/content list [category]\n/content send ID\n/content del ID"),
 "groups": ("👥 مدیریت گروه", "دستورات مدیریت در /help؛ اجرای عملیات نیازمند دسترسی ادمین ربات و کاربر است."),
 "fonts": ("🔤 فونت", "/font متن برای چند خروجی Unicode."),
 "translate": ("🌐 ترجمه", "/translate en متن؛ تشخیص زبان و Cache خودکار است."),
 "ai": ("🧠 هوش مصنوعی", "/ai پرسش، /ai summarize متن، /ai translate متن؛ بدون API key غیرفعال می‌ماند."),
 "voice": ("🎙️ صدا", "/tts متن؛ برای STT روی Voice با /stt پاسخ دهید."),
 "image": ("🖼️ تصویر", "روی عکس Reply کنید: /imageinfo یا /resize 800 600"),
 "currency": ("💰 ارز", "/currency USD EUR [amount]"),
 "tools": ("🧮 ابزارها", "/calc (2+3)*4 یا /percent 20 150"),
 "games": ("🎮 بازی‌ها", "/game برای پروفایل، فروشگاه، ماموریت، پاداش روزانه و رتبه‌بندی."),
 "meow": ("🐱 بازی میویی", "/meow برای بازکردن بازی چندکاربره و دکمه‌های آن."),
 "stats": ("📊 آمار", "/stats آمار عمومی؛ /game stats و /meow stats آمار بازی."),
 "help": ("ℹ️ راهنما", HELP_TEXT),
}


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ بازگشت", callback_data="menu:home")]])


@router.callback_query(F.data == "menu:home")
async def home(call: CallbackQuery) -> None:
    await call.message.edit_text("<b>پنل اصلی</b>\nیک بخش را انتخاب کنید:", reply_markup=main_keyboard())
    await call.answer()


@router.callback_query(F.data.startswith("menu:"))
async def page(call: CallbackQuery, db: Database) -> None:
    key = call.data.split(":", 1)[1]
    title, body = PAGES.get(key, ("بخش ناشناخته", "این بخش در دسترس نیست."))
    await call.message.edit_text(f"<b>{title}</b>\n\n{body}", reply_markup=back_keyboard())
    await call.answer()
