from uuid import uuid4
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from core.scheduler import SchedulerService
from database.db import Database

router = Router(name="scheduler")

@router.message(Command("schedule"))
async def schedule(message: Message, db: Database, scheduler: SchedulerService) -> None:
    parts = (message.text or "").split(maxsplit=3)
    if len(parts) < 2:
        await message.answer("/schedule once 2026-12-31T20:00:00+00:00 متن\n/schedule daily 12:30 متن\n/schedule weekly mon@12:30 متن\n/schedule list|del|pause|resume [ID]"); return
    action = parts[1]
    if action in {"once", "daily", "weekly"} and len(parts) == 4:
        job_id = uuid4().hex[:10]
        try: await scheduler.add_job(job_id, message.from_user.id, message.chat.id, action, parts[2], {"text": parts[3]})
        except (ValueError, TypeError) as exc: await message.answer(f"زمان نامعتبر: {exc}"); return
        await message.answer(f"Job ساخته شد: <code>{job_id}</code>")
    elif action == "list":
        rows = await db.fetchall("SELECT id,schedule_type,schedule_value,enabled FROM scheduled_jobs WHERE owner_id=?", (message.from_user.id,))
        await message.answer("\n".join(f"{r['id']} {r['schedule_type']} {r['schedule_value']} {'▶️' if r['enabled'] else '⏸'}" for r in rows) or "خالی است.")
    elif action in {"del", "pause", "resume"} and len(parts) >= 3:
        ok = await scheduler.remove_job(parts[2], message.from_user.id) if action == "del" else await scheduler.set_job_enabled(parts[2], message.from_user.id, action == "resume")
        await message.answer("انجام شد." if ok else "Job پیدا نشد.")
    else: await message.answer("ساختار دستور نامعتبر است.")
