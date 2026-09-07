from aiogram import F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.types import Message
from database.db import Database

router = Router(name="autoreply")

@router.message(Command("autoreply"))
async def manage(message: Message, db: Database) -> None:
    raw = (message.text or "").split(maxsplit=2)
    if len(raw) < 2:
        await message.answer("/autoreply add trigger | response\n/autoreply list\n/autoreply del ID\n/autoreply toggle ID")
        return
    action = raw[1]
    if action == "add" and len(raw) == 3 and "|" in raw[2]:
        trigger, response = (part.strip() for part in raw[2].split("|", 1))
        source = message.reply_to_message
        response_type, file_id = "text", None
        if source and source.photo:
            response_type, file_id = "photo", source.photo[-1].file_id
        elif source and source.video:
            response_type, file_id = "video", source.video.file_id
        elif source and source.document:
            response_type, file_id = "document", source.document.file_id
        if not trigger or (not response and not file_id) or len(trigger) > 100 or len(response) > 4000:
            await message.answer("طول ورودی نامعتبر است."); return
        scope = "private" if message.chat.type == "private" else "group"
        await db.execute("""INSERT OR REPLACE INTO autoreplies
            (owner_id,chat_id,scope,trigger,response_type,response,file_id) VALUES(?,?,?,?,?,?,?)""",
            (message.from_user.id, message.chat.id, scope, trigger.casefold(), response_type, response, file_id))
        await message.answer("پاسخ خودکار ذخیره شد.")
    elif action == "list":
        rows = await db.fetchall("SELECT id,trigger,response,enabled FROM autoreplies WHERE owner_id=? ORDER BY id DESC LIMIT 50", (message.from_user.id,))
        await message.answer("\n".join(f"#{r['id']} {'✅' if r['enabled'] else '⛔'} {r['trigger']} → {r['response'][:40]}" for r in rows) or "خالی است.")
    elif action in {"del", "toggle"} and len(raw) == 3 and raw[2].isdigit():
        if action == "del":
            await db.execute("DELETE FROM autoreplies WHERE id=? AND owner_id=?", (int(raw[2]), message.from_user.id))
        else:
            await db.execute("UPDATE autoreplies SET enabled=1-enabled WHERE id=? AND owner_id=?", (int(raw[2]), message.from_user.id))
        await message.answer("انجام شد.")
    else:
        await message.answer("دستور نامعتبر است.")

@router.message(F.text & ~F.text.startswith("/"))
async def reply(message: Message, db: Database) -> None:
    scope = "private" if message.chat.type == "private" else "group"
    row = await db.fetchone("""SELECT * FROM autoreplies WHERE enabled=1 AND trigger=?
        AND scope IN (?, 'all') AND (chat_id=? OR chat_id=0) ORDER BY chat_id DESC LIMIT 1""",
        ((message.text or "").casefold().strip(), scope, message.chat.id))
    if not row:
        raise SkipHandler
    if row["response_type"] == "photo":
        await message.reply_photo(row["file_id"], caption=row["response"])
    elif row["response_type"] == "video":
        await message.reply_video(row["file_id"], caption=row["response"])
    elif row["response_type"] == "document":
        await message.reply_document(row["file_id"], caption=row["response"])
    else:
        await message.reply(row["response"])
