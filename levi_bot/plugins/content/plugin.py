from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database.db import Database

router=Router(name="content")

def media_of(msg: Message):
    if msg.photo: return "photo",msg.photo[-1].file_id,msg.caption
    if msg.video: return "video",msg.video.file_id,msg.caption
    if msg.document: return "document",msg.document.file_id,msg.caption
    return "text",None,msg.text

@router.message(Command("content"))
async def content(message: Message,db:Database)->None:
    p=(message.text or "").split(maxsplit=4)
    if len(p)<2: await message.answer("/content save CATEGORY TITLE | TEXT (یا Reply رسانه)\n/content list [CATEGORY]\n/content send ID\n/content del ID"); return
    if p[1]=="save" and len(p)>=4:
        title,_,body=p[3].partition("|"); source=message.reply_to_message or message
        ctype,file_id,media_body=media_of(source); body=(body.strip() or media_body or "")[:4000]
        await db.execute("INSERT INTO content(owner_id,category,title,content_type,body,file_id) VALUES(?,?,?,?,?,?)",(message.from_user.id,p[2][:50],title.strip()[:100],ctype,body,file_id)); await message.answer("ذخیره شد.")
    elif p[1]=="list":
        params=[message.from_user.id]; sql="SELECT id,category,title,content_type FROM content WHERE owner_id=?"
        if len(p)>2: sql+=" AND category=?"; params.append(p[2])
        rows=await db.fetchall(sql+" ORDER BY id DESC LIMIT 50",params); await message.answer("\n".join(f"#{r['id']} [{r['category']}] {r['title']} ({r['content_type']})" for r in rows) or "خالی است.")
    elif p[1] in {"send","del"} and len(p)>2 and p[2].isdigit():
        row=await db.fetchone("SELECT * FROM content WHERE id=? AND owner_id=?",(int(p[2]),message.from_user.id))
        if not row: await message.answer("پیدا نشد."); return
        if p[1]=="del": await db.execute("DELETE FROM content WHERE id=?",(row["id"],)); await message.answer("حذف شد."); return
        methods={"photo":message.answer_photo,"video":message.answer_video,"document":message.answer_document}
        if row["content_type"]=="text": await message.answer(row["body"])
        else: await methods[row["content_type"]](row["file_id"],caption=row["body"])
