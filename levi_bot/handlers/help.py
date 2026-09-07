"""Help and command index."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")

HELP_TEXT = """<b>راهنمای دستورات</b>
/start /help /ping /alive /stats /profile /settings
/autoreply /filter /reaction /forward /schedule /content
/font متن | /translate زبان متن | /ai پرسش | /tts متن
/imageinfo (روی تصویر Reply) | /currency USD EUR | /calc عبارت
/rules /setrules /warn /unwarn /ban /unban /mute /unmute /kick /pin
/tag متن | /tagstop
/game /daily /inventory /shop /buy /sell /quest /leaderboard
/meow و زیر‌دستورهای profile, balance, inventory, fish, autofish, cook,
autocook, factory, autofactory, shop, buy, sell, quest, claim,
level, stats, leaderboard, auto, stop

برای جزئیات هر بخش، دکمه همان بخش در /start را انتخاب کنید."""


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT)
