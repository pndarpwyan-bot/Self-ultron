"""Dispatcher middlewares and router assembly."""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import TelegramObject, Update

from core.loader import PluginReport, load_plugins
from core.rate_limit import RateLimiter
from database.db import Database
from handlers import admin, callbacks, help, start

logger = logging.getLogger(__name__)


class ContextMiddleware(BaseMiddleware):
    def __init__(self, db: Database, limiter: RateLimiter) -> None:
        self.db, self.limiter = db, limiter

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        data["db"] = self.db
        data["rate_limiter"] = self.limiter
        user = data.get("event_from_user")
        chat = data.get("event_chat")
        if user:
            await self.db.upsert_user(user.id, user.username, user.full_name)
            blocked = await self.db.fetchone("SELECT is_blocked FROM users WHERE user_id=?", (user.id,))
            if blocked and blocked["is_blocked"]:
                return None
            is_command = bool(getattr(event, "text", "") and getattr(event, "text", "").startswith("/"))
            await self.db.record_activity(user.id, is_command)
        if chat:
            await self.db.upsert_chat(chat.id, getattr(chat, "title", None), chat.type)
        await self.db.increment_stat("updates")
        return await handler(event, data)


class ErrorMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Unhandled update error")
            db: Database | None = data.get("db")
            if db:
                await db.increment_stat("errors")
            return None


def build_dispatcher(db: Database, scheduler: Any) -> tuple[Dispatcher, PluginReport]:
    dp = Dispatcher(db=db, scheduler=scheduler)
    limiter = RateLimiter()
    dp.update.outer_middleware(ErrorMiddleware())
    dp.update.outer_middleware(ContextMiddleware(db, limiter))
    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(admin.router)
    dp.include_router(callbacks.router)
    report = load_plugins(dp)
    return dp, report
