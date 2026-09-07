"""Persistent multi-user Meow fishing/economy game."""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from database.db import Database

router=Router(name="meow")

def menu()->InlineKeyboardMarkup:
 return InlineKeyboardMarkup(inline_keyboard=[
  [InlineKeyboardButton(text="🐱 پروفایل",callback_data="meow:profile"),InlineKeyboardButton(text="🎣 ماهیگیری",callback_data="meow:fish")],
  [InlineKeyboardButton(text="🎒 انبار",callback_data="meow:inventory"),InlineKeyboardButton(text="💵 فروش ماهی",callback_data="meow:sellfish")],
  [InlineKeyboardButton(text="🍳 آشپزی",callback_data="meow:cook"),InlineKeyboardButton(text="🏭 کارخانه",callback_data="meow:factory")],
  [InlineKeyboardButton(text="🛒 فروشگاه",callback_data="meow:shop"),InlineKeyboardButton(text="🎯 ماموریت",callback_data="meow:quest")],
  [InlineKeyboardButton(text="🤖 خودکار",callback_data="meow:auto"),InlineKeyboardButton(text="🏆 رتبه‌بندی",callback_data="meow:leaderboard")],
  [InlineKeyboardButton(text="⬅️ بازگشت",callback_data="menu:home")]])

async def ensure(db:Database,uid:int): await db.ensure_game_profiles(uid)
async def profile(db:Database,uid:int)->str:
 await ensure(db,uid); p=await db.fetchone("SELECT * FROM meow_profiles WHERE user_id=?",(uid,)); f=await db.fetchone("SELECT COUNT(*) kinds,COALESCE(SUM(quantity),0) total FROM inventory WHERE user_id=? AND namespace='meow' AND quantity>0",(uid,))
 return f"<b>🐱 پروفایل میویی</b>\n💰 {p['balance']} سکه\n⭐ XP: {p['xp']}\n🏆 Level: {p['level']}\n🐟 ماهی‌ها: {f['total']} ({f['kinds']} نوع)"
async def inv_text(db:Database,uid:int)->str:
 rows=await db.fetchall("""SELECT i.item_code,i.quantity,COALESCE(f.name,i.item_code) name FROM inventory i LEFT JOIN fish f ON f.code=i.item_code WHERE i.user_id=? AND i.namespace='meow' AND i.quantity>0""",(uid,)); return "<b>🎒 انبار میویی</b>\n"+("\n".join(f"{r['name']}: {r['quantity']}" for r in rows) or "خالی")
async def cooldown(db:Database,uid:int,action:str,seconds:int)->int:
 now=datetime.now(timezone.utc); row=await db.fetchone("SELECT available_at FROM cooldowns WHERE user_id=? AND action=?",(uid,action))
 if row:
  left=(datetime.fromisoformat(row["available_at"])-now).total_seconds()
  if left>0:return int(left)+1
 await db.execute("INSERT INTO cooldowns(user_id,action,available_at) VALUES(?,?,?) ON CONFLICT(user_id,action) DO UPDATE SET available_at=excluded.available_at",(uid,action,(now+timedelta(seconds=seconds)).isoformat())); return 0
async def do_fish(db:Database,uid:int)->str:
 await ensure(db,uid); left=await cooldown(db,uid,"meow_fish",45)
 if left:return f"⏱️ {left} ثانیه تا ماهیگیری بعدی."
 p=await db.fetchone("SELECT level FROM meow_profiles WHERE user_id=?",(uid,)); rows=await db.fetchall("SELECT * FROM fish WHERE min_level<=?",(p["level"],)); weights={"معمولی":60,"کمیاب":25,"نادر":10,"افسانه‌ای":2}; fish=random.choices(rows,weights=[weights.get(r["rarity"],10) for r in rows],k=1)[0]
 await db.add_inventory(uid,fish["code"],1,"meow"); xp=random.randint(5,12); await db.execute("UPDATE meow_profiles SET xp=xp+?,level=1+(xp+?)/100 WHERE user_id=?",(xp,xp,uid)); await db.execute("INSERT INTO game_stats(user_id,key,value) VALUES(?,'fish_caught',1) ON CONFLICT(user_id,key) DO UPDATE SET value=value+1",(uid,)); await db.execute("INSERT INTO user_quests(user_id,quest_code,progress) VALUES(?,'fish_10',1) ON CONFLICT(user_id,quest_code) DO UPDATE SET progress=progress+1",(uid,)); return f"🎣 یک {fish['name']} ({fish['rarity']}) گرفتی! +{xp} XP"
async def sell_all(db:Database,uid:int)->str:
 await ensure(db,uid)
 async with db.transaction() as conn:
  rows=await (await conn.execute("SELECT i.item_code,i.quantity,f.value FROM inventory i JOIN fish f ON f.code=i.item_code WHERE i.user_id=? AND i.namespace='meow' AND i.quantity>0",(uid,))).fetchall(); total=sum(r["quantity"]*r["value"] for r in rows)
  if not total:return "ماهی برای فروش ندارید."
  await conn.execute("UPDATE inventory SET quantity=0 WHERE user_id=? AND namespace='meow' AND item_code IN (SELECT code FROM fish)",(uid,)); await conn.execute("UPDATE meow_profiles SET balance=balance+? WHERE user_id=?",(total,uid)); await conn.execute("INSERT INTO transactions(user_id,namespace,kind,amount,description) VALUES(?,'meow','sell',?,'all fish')",(uid,total))
 return f"💵 همه ماهی‌ها به {total} سکه فروخته شدند."
async def auto_set(db:Database,uid:int,kind:str,enabled:bool)->str:
 valid={"autofish":180,"autocook":300,"autofactory":240,"autosell":600,"autoquest":900}
 if kind not in valid:return "نوع Auto نامعتبر است."
 await ensure(db,uid)
 if enabled:
  next_run=(datetime.now(timezone.utc)+timedelta(seconds=valid[kind])).isoformat(); await db.execute("INSERT INTO auto_tasks(user_id,task_type,enabled,interval_seconds,next_run) VALUES(?,?,?,?,?) ON CONFLICT(user_id,task_type) DO UPDATE SET enabled=1,interval_seconds=excluded.interval_seconds,next_run=excluded.next_run",(uid,kind,1,valid[kind],next_run)); return f"🤖 {kind} روشن شد."
 await db.execute("UPDATE auto_tasks SET enabled=0 WHERE user_id=? AND task_type=?",(uid,kind)); return f"⛔ {kind} خاموش شد."
async def text_for(action:str,db:Database,uid:int)->str:
 await ensure(db,uid)
 if action in {"profile","balance","level"}:return await profile(db,uid)
 if action=="inventory":return await inv_text(db,uid)
 if action=="fish":return await do_fish(db,uid)
 if action=="sellfish":return await sell_all(db,uid)
 if action=="shop":
  rows=await db.fetchall("SELECT code,name,price,sell_price FROM items"); return "<b>🛒 فروشگاه</b>\n"+"\n".join(f"{r['code']} {r['name']}: {r['price']}" for r in rows)+"\n/meow buy CODE QTY"
 if action=="cook":
  row=await db.fetchone("SELECT quantity FROM inventory WHERE user_id=? AND item_code='sardine' AND namespace='meow'",(uid,))
  if not row or row["quantity"]<2:return "برای پخت، ۲ ساردین لازم است."
  await db.add_inventory(uid,"sardine",-2,"meow"); await db.add_inventory(uid,"grilled_fish",1,"meow"); return "🍳 یک ماهی کبابی آماده شد."
 if action=="factory":
  f=await db.fetchone("SELECT * FROM factory WHERE user_id=?",(uid,)); return f"<b>🏭 کارخانه</b>\nسطح: {f['level']}\nظرفیت: {f['slots']}\nتولید کل: {f['produced']}"
 if action=="quest":
  q=await db.fetchone("SELECT progress,claimed FROM user_quests WHERE user_id=? AND quest_code='fish_10'",(uid,)); return f"🎯 صید ۱۰ ماهی: {q['progress'] if q else 0}/10\n/meow claim"
 if action=="leaderboard":
  rows=await db.fetchall("SELECT user_id,level,xp,balance FROM meow_profiles ORDER BY level DESC,xp DESC,balance DESC LIMIT 10"); return "<b>🏆 برترین میوها</b>\n"+"\n".join(f"{i}. <code>{r['user_id']}</code> L{r['level']} 💰{r['balance']}" for i,r in enumerate(rows,1))
 if action=="stats":
  rows=await db.fetchall("SELECT key,value FROM game_stats WHERE user_id=?",(uid,)); return "<b>📊 آمار</b>\n"+("\n".join(f"{r['key']}: {r['value']}" for r in rows) or "هنوز آماری نیست.")
 if action=="auto":
  rows=await db.fetchall("SELECT task_type,enabled,next_run FROM auto_tasks WHERE user_id=?",(uid,)); return "<b>🤖 Auto Tasks</b>\n"+("\n".join(f"{r['task_type']}: {'on' if r['enabled'] else 'off'}" for r in rows) or "خالی")+"\n/meow autofish on"
 return "دستور ناشناخته؛ /meow را اجرا کنید."

@router.message(Command("meow"))
async def meow(message:Message,db:Database)->None:
 p=(message.text or "").split(); action=p[1].lower() if len(p)>1 else "profile"; uid=message.from_user.id
 if action in {"autofish","autocook","autofactory","autosell","autoquest"}: await message.answer(await auto_set(db,uid,action,len(p)<3 or p[2]=="on"),reply_markup=menu()); return
 if action=="stop":
  kind=p[2] if len(p)>2 else None
  if kind: await message.answer(await auto_set(db,uid,kind,False),reply_markup=menu())
  else: await db.execute("UPDATE auto_tasks SET enabled=0 WHERE user_id=?",(uid,)); await message.answer("همه Auto Taskها متوقف شدند.",reply_markup=menu())
  return
 if action=="claim":
  q=await db.fetchone("SELECT progress,claimed FROM user_quests WHERE user_id=? AND quest_code='fish_10'",(uid,))
  if not q or q["progress"]<10 or q["claimed"]: await message.answer("ماموریت آماده دریافت نیست."); return
  await db.execute("UPDATE user_quests SET claimed=1 WHERE user_id=? AND quest_code='fish_10'",(uid,)); await db.execute("UPDATE meow_profiles SET balance=balance+200,xp=xp+80 WHERE user_id=?",(uid,)); await message.answer("🎁 ۲۰۰ سکه و ۸۰ XP دریافت شد."); return
 if action in {"buy","sell"}:
  if len(p)<3: await message.answer("/meow buy CODE [QTY]"); return
  item=await db.fetchone("SELECT * FROM items WHERE code=?",(p[2],)); qty=int(p[3]) if len(p)>3 and p[3].isdigit() else 1
  if not item or not 1<=qty<=100: await message.answer("کالا/تعداد نامعتبر است."); return
  await ensure(db,uid); buying=action=="buy"; inv=await db.fetchone("SELECT quantity FROM inventory WHERE user_id=? AND item_code=? AND namespace='meow'",(uid,p[2])); prof=await db.fetchone("SELECT balance FROM meow_profiles WHERE user_id=?",(uid,)); cost=(item["price"] if buying else item["sell_price"])*qty
  if buying and prof["balance"]<cost: await message.answer("موجودی سکه کافی نیست."); return
  if not buying and (not inv or inv["quantity"]<qty): await message.answer("موجودی کالا کافی نیست."); return
  await db.execute("UPDATE meow_profiles SET balance=balance+? WHERE user_id=?",(-cost if buying else cost,uid)); await db.add_inventory(uid,p[2],qty if buying else -qty,"meow"); await message.answer("معامله انجام شد."); return
 await message.answer(await text_for(action,db,uid),reply_markup=menu())

@router.callback_query(F.data.startswith("meow:"))
async def callbacks(call:CallbackQuery,db:Database)->None:
 action=call.data.split(":",1)[1]
 await call.message.edit_text(await text_for(action,db,call.from_user.id),reply_markup=menu()); await call.answer()
