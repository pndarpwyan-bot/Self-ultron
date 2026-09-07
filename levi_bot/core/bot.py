"""Application lifecycle."""
from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Settings
from core.router import build_dispatcher
from core.scheduler import SchedulerService
from database.db import Database

logger = logging.getLogger(__name__)


async def run_bot(settings: Settings) -> None:
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    db = Database(settings.database_path)
    await db.connect()
    if settings.admin_id:
        await db.execute("INSERT OR IGNORE INTO admins(user_id) VALUES(?)", (settings.admin_id,))
    scheduler = SchedulerService(bot, db)
    dispatcher, report = build_dispatcher(db, scheduler)
    logger.info("Plugins loaded=%d failed=%d", len(report.loaded), len(report.failed))
    await scheduler.start()
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        await dispatcher.start_polling(bot, settings=settings, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        await scheduler.shutdown()
        await db.close()
        await bot.session.close()
