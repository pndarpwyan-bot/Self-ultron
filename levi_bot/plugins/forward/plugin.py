from aiogram import F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.types import Message
from database.db import Database

router = Router(name="forward")

@router.message(Command("forward"))
async def manage(message: Message, db: Database) -> None:
    p=(message.text or "").split()
    if len(p)<2: await message.answer("/forward add SOURCE DEST\n/forward list\n/forward del ID\n/forward stop"); return
    if p[1]=="add" and len(p)==4 and p[2].lstrip("-").isdigit() and p[3].lstrip("-").isdigit():
        await db.execute("INSERT OR IGNORE INTO forward_rules(owner_id,source_chat_id,destination_chat_id) VALUES(?,?,?)",(message.from_user.id,int(p[2]),int(p[3]))); await message.answer("قانون ذخیره شد.")
    elif p[1]=="list":
        rows=await db.fetchall("SELECT * FROM forward_rules WHERE owner_id=?",(message.from_user.id,)); await message.answer("\n".join(f"#{r['id']} {r['source_chat_id']} → {r['destination_chat_id']}" for r in rows) or "خالی است.")
    elif p[1]=="del" and len(p)==3 and p[2].isdigit(): await db.execute("DELETE FROM forward_rules WHERE id=? AND owner_id=?",(int(p[2]),message.from_user.id)); await message.answer("حذف شد.")
    elif p[1]=="stop": await db.execute("UPDATE forward_rules SET enabled=0 WHERE owner_id=?",(message.from_user.id,)); await message.answer("همه متوقف شدند.")

@router.message(F.chat.type.in_({"group","supergroup","channel"}))
async def auto_forward(message: Message, db: Database) -> None:
    rows=await db.fetchall("SELECT destination_chat_id FROM forward_rules WHERE source_chat_id=? AND enabled=1 LIMIT 10",(message.chat.id,))
    if not rows: raise SkipHandler
    for row in rows:
        try: await message.forward(row["destination_chat_id"])
        except Exception: await db.increment_stat("errors")
