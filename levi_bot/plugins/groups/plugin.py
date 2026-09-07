import asyncio,re
from datetime import datetime,timedelta,timezone
from aiogram import F,Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.types import ChatPermissions,Message
from database.db import Database
router=Router(name="groups")
async def admin(message:Message)->bool:
 if message.chat.type=="private": return False
 m=await message.bot.get_chat_member(message.chat.id,message.from_user.id); return m.status in {"creator","administrator"}
def target(message:Message): return message.reply_to_message.from_user if message.reply_to_message else None
@router.message(Command("ban","unban","kick","mute","unmute"))
async def moderation(message:Message)->None:
 if not await admin(message): await message.answer("فقط مدیر گروه مجاز است."); return
 user=target(message)
 if not user: await message.answer("دستور را روی پیام کاربر Reply کنید."); return
 cmd=(message.text or "").split()[0].split("@")[0][1:]
 try:
  if cmd=="ban": await message.chat.ban(user.id)
  elif cmd=="unban": await message.chat.unban(user.id,only_if_banned=True)
  elif cmd=="kick": await message.chat.ban(user.id); await message.chat.unban(user.id)
  elif cmd=="mute": await message.chat.restrict(user.id,ChatPermissions(can_send_messages=False),until_date=datetime.now(timezone.utc)+timedelta(hours=1))
  else: await message.chat.restrict(user.id,ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_invite_users=True))
  await message.answer("انجام شد.")
 except Exception as e: await message.answer(f"عملیات ممکن نیست؛ دسترسی ربات را بررسی کنید: {e}")
@router.message(Command("warn","unwarn"))
async def warnings(message:Message,db:Database)->None:
 if not await admin(message) or not target(message): return
 delta=1 if message.text.startswith("/warn") else -1
 await db.execute("""INSERT INTO warnings(chat_id,user_id,count) VALUES(?,?,?) ON CONFLICT(chat_id,user_id)
 DO UPDATE SET count=MAX(0,count+?)""",(message.chat.id,target(message).id,max(0,delta),delta))
 row=await db.fetchone("SELECT count FROM warnings WHERE chat_id=? AND user_id=?",(message.chat.id,target(message).id)); await message.answer(f"اخطارها: {row['count']}")
@router.message(Command("pin"))
async def pin(message:Message)->None:
 if await admin(message) and message.reply_to_message:
  try: await message.bot.pin_chat_message(message.chat.id,message.reply_to_message.message_id); await message.answer("سنجاق شد.")
  except Exception as e: await message.answer(f"خطا: {e}")
@router.message(Command("setrules"))
async def setrules(message:Message,db:Database)->None:
 if not await admin(message): return
 text=(message.text or "").partition(" ")[2][:3500]; await db.execute("INSERT INTO chat_settings(chat_id,key,value) VALUES(?,?,?) ON CONFLICT(chat_id,key) DO UPDATE SET value=excluded.value",(message.chat.id,"rules",text)); await message.answer("قوانین ذخیره شد.")
@router.message(Command("rules"))
async def rules(message:Message,db:Database)->None:
 row=await db.fetchone("SELECT value FROM chat_settings WHERE chat_id=? AND key='rules'",(message.chat.id,)); await message.answer(row["value"] if row else "قوانینی ثبت نشده است.")
@router.message(Command("tag"))
async def tag(message:Message,db:Database)->None:
 if not await admin(message): return
 text=(message.text or "").partition(" ")[2] or "توجه"
 rows=await db.fetchall("SELECT user_id,full_name FROM users ORDER BY last_seen DESC LIMIT 50")
 for i in range(0,len(rows),5):
  enabled=await db.get_setting(message.from_user.id,f"tag:{message.chat.id}","on")
  if enabled=="off": break
  chunk=" ".join(f'<a href="tg://user?id={r["user_id"]}">{r["full_name"][:20]}</a>' for r in rows[i:i+5]); await message.answer(f"{text}\n{chunk}"); await asyncio.sleep(1.2)
@router.message(Command("tagstop"))
async def tagstop(message:Message,db:Database)->None: await db.set_setting(message.from_user.id,f"tag:{message.chat.id}","off"); await message.answer("Tag متوقف شد.")
@router.message(F.text.regexp(r"(?:https?://|t\.me/)",flags=re.I))
async def anti_link(message:Message,db:Database)->None:
 enabled=await db.fetchone("SELECT value FROM chat_settings WHERE chat_id=? AND key='antilink'",(message.chat.id,))
 if not enabled or enabled["value"]!="on": raise SkipHandler
 if await admin(message): raise SkipHandler
 try: await message.delete()
 except Exception: pass
