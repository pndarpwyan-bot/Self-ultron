from aiogram import F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.types import Message
from database.db import Database

router = Router(name="filter")

async def user_is_admin(message: Message) -> bool:
    if message.chat.type == "private": return True
    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in {"creator", "administrator"}

@router.message(Command("filter"))
async def manage(message: Message, db: Database) -> None:
    if not await user_is_admin(message):
        await message.answer("فقط مدیر گفتگو مجاز است."); return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("/filter add WORD [delete|warn|mute]\n/filter list\n/filter del ID"); return
    if parts[1] == "add" and len(parts) >= 3:
        action = parts[3] if len(parts) > 3 and parts[3] in {"delete", "warn", "mute"} else "delete"
        await db.execute("INSERT OR REPLACE INTO filters(owner_id,chat_id,word,action) VALUES(?,?,?,?)",
                         (message.from_user.id, message.chat.id, parts[2].casefold(), action))
        await message.answer("فیلتر افزوده شد.")
    elif parts[1] == "list":
        rows = await db.fetchall("SELECT * FROM filters WHERE chat_id=?", (message.chat.id,))
        await message.answer("\n".join(f"#{r['id']} {r['word']} ({r['action']})" for r in rows) or "خالی است.")
    elif parts[1] == "del" and len(parts) > 2 and parts[2].isdigit():
        await db.execute("DELETE FROM filters WHERE id=? AND chat_id=?", (int(parts[2]), message.chat.id)); await message.answer("حذف شد.")

@router.message(F.text & ~F.text.startswith("/"))
async def enforce(message: Message, db: Database) -> None:
    rows = await db.fetchall("SELECT * FROM filters WHERE chat_id=? AND enabled=1", (message.chat.id,))
    match = next((r for r in rows if r["word"] in (message.text or "").casefold()), None)
    if not match: raise SkipHandler
    try: await message.delete()
    except Exception: return
    if match["action"] == "warn":
        await db.execute("""INSERT INTO warnings(chat_id,user_id,count) VALUES(?,?,1)
            ON CONFLICT(chat_id,user_id) DO UPDATE SET count=count+1""", (message.chat.id, message.from_user.id))
