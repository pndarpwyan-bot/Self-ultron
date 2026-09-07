"""Persistent APScheduler adapter for messages and game auto tasks."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from database.db import Database

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, bot: Bot, db: Database) -> None:
        self.bot = bot
        self.db = db
        self.scheduler = AsyncIOScheduler(timezone="UTC")

    async def start(self) -> None:
        rows = await self.db.fetchall("SELECT * FROM scheduled_jobs WHERE enabled=1")
        for row in rows:
            try:
                self._register(dict(row))
            except Exception:
                logger.exception("Could not restore job %s", row["id"])
        self.scheduler.add_job(self.process_auto_tasks, "interval", seconds=30, id="auto_tasks", replace_existing=True)
        self.scheduler.start()

    async def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def _trigger(self, schedule_type: str, value: str):
        if schedule_type == "once":
            return DateTrigger(run_date=datetime.fromisoformat(value))
        if schedule_type == "daily":
            hour, minute = map(int, value.split(":"))
            return CronTrigger(hour=hour, minute=minute)
        if schedule_type == "weekly":
            day, clock = value.split("@", 1)
            hour, minute = map(int, clock.split(":"))
            return CronTrigger(day_of_week=day, hour=hour, minute=minute)
        if schedule_type == "interval":
            return IntervalTrigger(seconds=max(30, int(value)))
        raise ValueError("schedule_type نامعتبر است")

    def _register(self, row: dict[str, Any]) -> None:
        self.scheduler.add_job(
            self.run_job,
            self._trigger(row["schedule_type"], row["schedule_value"]),
            args=[row["id"]], id=f"user:{row['id']}", replace_existing=True,
            misfire_grace_time=300, coalesce=True, max_instances=1,
        )

    async def add_job(self, job_id: str, owner_id: int, chat_id: int, schedule_type: str,
                      schedule_value: str, payload: dict[str, Any], job_type: str = "message") -> None:
        data = {"id": job_id, "owner_id": owner_id, "chat_id": chat_id, "schedule_type": schedule_type,
                "schedule_value": schedule_value, "payload": self.db.json(payload), "job_type": job_type}
        self._trigger(schedule_type, schedule_value)
        await self.db.execute(
            """INSERT INTO scheduled_jobs(id,owner_id,chat_id,job_type,schedule_type,schedule_value,payload)
            VALUES(?,?,?,?,?,?,?)""",
            (job_id, owner_id, chat_id, job_type, schedule_type, schedule_value, data["payload"]),
        )
        self._register(data)

    async def run_job(self, job_id: str) -> None:
        row = await self.db.fetchone("SELECT * FROM scheduled_jobs WHERE id=? AND enabled=1", (job_id,))
        if not row:
            return
        try:
            payload = json.loads(row["payload"])
            if row["job_type"] == "message":
                await self.bot.send_message(row["chat_id"], payload["text"])
            await self.db.increment_stat("scheduled_jobs_run")
            if row["schedule_type"] == "once":
                await self.db.execute("UPDATE scheduled_jobs SET enabled=0 WHERE id=?", (job_id,))
        except Exception:
            logger.exception("Scheduled job %s failed", job_id)
            await self.db.increment_stat("errors")

    async def remove_job(self, job_id: str, owner_id: int) -> bool:
        row = await self.db.fetchone("SELECT id FROM scheduled_jobs WHERE id=? AND owner_id=?", (job_id, owner_id))
        if not row:
            return False
        try:
            self.scheduler.remove_job(f"user:{job_id}")
        except Exception:
            pass
        await self.db.execute("DELETE FROM scheduled_jobs WHERE id=?", (job_id,))
        return True

    async def set_job_enabled(self, job_id: str, owner_id: int, enabled: bool) -> bool:
        row = await self.db.fetchone("SELECT * FROM scheduled_jobs WHERE id=? AND owner_id=?", (job_id, owner_id))
        if not row:
            return False
        await self.db.execute("UPDATE scheduled_jobs SET enabled=? WHERE id=?", (int(enabled), job_id))
        scheduler_id = f"user:{job_id}"
        try:
            self.scheduler.resume_job(scheduler_id) if enabled else self.scheduler.pause_job(scheduler_id)
        except Exception:
            if enabled:
                self._register(dict(row))
        return True

    async def process_auto_tasks(self) -> None:
        rows = await self.db.fetchall(
            "SELECT * FROM auto_tasks WHERE enabled=1 AND datetime(next_run)<=datetime('now') LIMIT 100"
        )
        now = datetime.now(timezone.utc)
        for row in rows:
            try:
                await self._run_auto_task(dict(row))
                next_run = now + timedelta(seconds=max(60, row["interval_seconds"]))
                await self.db.execute("UPDATE auto_tasks SET next_run=? WHERE user_id=? AND task_type=?",
                                      (next_run.isoformat(), row["user_id"], row["task_type"]))
            except Exception:
                logger.exception("Auto task failed user=%s type=%s", row["user_id"], row["task_type"])
                await self.db.increment_stat("errors")

    async def _run_auto_task(self, task: dict[str, Any]) -> None:
        user_id, kind = task["user_id"], task["task_type"]
        await self.db.ensure_game_profiles(user_id)
        messages = {"autofish": "ماهیگیری خودکار انجام شد: ۱ ساردین.", "autocook": "آشپزی خودکار بررسی شد.",
                    "autofactory": "کارخانه ۲ سکه تولید کرد.", "autosell": "فروش خودکار بررسی شد.",
                    "autoquest": "ماموریت‌های خودکار بررسی شدند."}
        if kind == "autofish":
            await self.db.add_inventory(user_id, "sardine", 1, "meow")
        elif kind == "autofactory":
            await self.db.execute("UPDATE meow_profiles SET balance=balance+2 WHERE user_id=?", (user_id,))
        metadata = json.loads(task["metadata"] or "{}")
        if metadata.get("notify", True):
            try:
                await self.bot.send_message(user_id, messages.get(kind, "وظیفه خودکار انجام شد."))
            except Exception:
                logger.debug("Auto-task notification unavailable for %s", user_id)
