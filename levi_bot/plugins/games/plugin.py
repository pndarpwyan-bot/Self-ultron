"""A compact persistent RPG economy engine."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from database.db import Database

router = Router(name="games")

def keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 پروفایل", callback_data="game:profile"), InlineKeyboardButton(text="🎁 روزانه", callback_data="game:daily")],
        [InlineKeyboardButton(text="🎒 انبار", callback_data="game:inventory"), InlineKeyboardButton(text="🛒 فروشگاه", callback_data="game:shop")],
        [InlineKeyboardButton(text="🎯 ماموریت", callback_data="game:quest"), InlineKeyboardButton(text="🏆 رتبه‌بندی", callback_data="game:leaderboard")],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="menu:home")],
    ])

async def profile_text(db: Database, uid: int) -> str:
    await db.ensure_game_profiles(uid)
    p=await db.fetchone("SELECT * FROM game_profiles WHERE user_id=?",(uid,))
    return f"<b>🎮 پروفایل بازی</b>\nLevel: {p['level']}\nXP: {p['xp']}\nCoins: {p['coins']}"

@router.message(Command("game"))
async def game(message:Message,db:Database)->None: await message.answer(await profile_text(db,message.from_user.id),reply_markup=keyboard())

@router.message(Command("daily"))
async def daily(message:Message,db:Database)->None:
    await db.ensure_game_profiles(message.from_user.id)
    p=await db.fetchone("SELECT daily_claimed_at FROM game_profiles WHERE user_id=?",(message.from_user.id,)); now=datetime.now(timezone.utc)
    if p["daily_claimed_at"] and datetime.fromisoformat(p["daily_claimed_at"])>now-timedelta(hours=24): await message.answer("پاداش روزانه هنوز آماده نیست."); return
    await db.execute("UPDATE game_profiles SET coins=coins+100,xp=xp+20,daily_claimed_at=? WHERE user_id=?",(now.isoformat(),message.from_user.id)); await db.execute("INSERT INTO rewards(user_id,kind,amount) VALUES(?,?,?)",(message.from_user.id,"daily",100)); await message.answer("🎁 ۱۰۰ سکه و ۲۰ XP دریافت شد.")

@router.message(Command("inventory"))
async def inventory(message:Message,db:Database)->None:
 rows=await db.fetchall("SELECT item_code,quantity FROM inventory WHERE user_id=? AND namespace='game' AND quantity>0",(message.from_user.id,)); await message.answer("<b>🎒 انبار</b>\n"+("\n".join(f"{r['item_code']}: {r['quantity']}" for r in rows) or "خالی"))

@router.message(Command("shop"))
async def shop(message:Message,db:Database)->None:
 rows=await db.fetchall("SELECT code,name,price,sell_price FROM items"); await message.answer("<b>🛒 فروشگاه</b>\n"+"\n".join(f"{r['code']} — {r['name']}: خرید {r['price']} / فروش {r['sell_price']}" for r in rows)+"\n/buy CODE [QTY]")

@router.message(Command("buy","sell"))
async def trade(message:Message,db:Database)->None:
 p=(message.text or "").split(); qty=int(p[2]) if len(p)>2 and p[2].isdigit() else 1
 if len(p)<2 or not 1<=qty<=100: await message.answer("/buy CODE [QTY] یا /sell CODE [QTY]"); return
 await db.ensure_game_profiles(message.from_user.id); item=await db.fetchone("SELECT * FROM items WHERE code=?",(p[1],))
 if not item: await message.answer("کالا پیدا نشد."); return
 buying=message.text.startswith("/buy"); price=item["price"] if buying else item["sell_price"]
 async with db.transaction() as conn:
  prof=await (await conn.execute("SELECT coins FROM game_profiles WHERE user_id=?",(message.from_user.id,))).fetchone()
  inv=await (await conn.execute("SELECT quantity FROM inventory WHERE user_id=? AND item_code=? AND namespace='game'",(message.from_user.id,p[1]))).fetchone()
  if buying and prof["coins"]<price*qty: await message.answer("سکه کافی نیست."); return
  if not buying and (not inv or inv["quantity"]<qty): await message.answer("موجودی کافی نیست."); return
  delta=-price*qty if buying else price*qty
  await conn.execute("UPDATE game_profiles SET coins=coins+? WHERE user_id=?",(delta,message.from_user.id))
  await conn.execute("INSERT INTO inventory(user_id,item_code,quantity,namespace) VALUES(?,?,?,'game') ON CONFLICT(user_id,item_code,namespace) DO UPDATE SET quantity=quantity+excluded.quantity",(message.from_user.id,p[1],qty if buying else -qty))
  await conn.execute("INSERT INTO transactions(user_id,namespace,kind,amount,description) VALUES(?,'game',?,?,?)",(message.from_user.id,"buy" if buying else "sell",delta,p[1]))
 await message.answer("معامله انجام شد.")

@router.message(Command("quest"))
async def quest(message:Message,db:Database)->None:
 rows=await db.fetchall("SELECT * FROM quests WHERE active=1"); await message.answer("<b>🎯 ماموریت‌ها</b>\n"+"\n".join(f"{r['code']}: {r['title']} — {r['reward_coins']} سکه" for r in rows))

@router.message(Command("leaderboard"))
async def leaderboard(message:Message,db:Database)->None:
 rows=await db.fetchall("SELECT user_id,level,xp,coins FROM game_profiles ORDER BY level DESC,xp DESC LIMIT 10"); await message.answer("<b>🏆 برترین‌ها</b>\n"+"\n".join(f"{i}. <code>{r['user_id']}</code> L{r['level']} XP{r['xp']}" for i,r in enumerate(rows,1)))

@router.callback_query(F.data.startswith("game:"))
async def callbacks(call:CallbackQuery,db:Database)->None:
 action=call.data.split(":")[1]; uid=call.from_user.id
 if action=="profile": text=await profile_text(db,uid)
 elif action=="daily":
  await db.ensure_game_profiles(uid); p=await db.fetchone("SELECT daily_claimed_at FROM game_profiles WHERE user_id=?",(uid,)); now=datetime.now(timezone.utc)
  if p["daily_claimed_at"] and datetime.fromisoformat(p["daily_claimed_at"])>now-timedelta(hours=24): text="پاداش روزانه هنوز آماده نیست."
  else: await db.execute("UPDATE game_profiles SET coins=coins+100,xp=xp+20,daily_claimed_at=? WHERE user_id=?",(now.isoformat(),uid)); text="🎁 ۱۰۰ سکه و ۲۰ XP دریافت شد."
 elif action=="inventory":
  rows=await db.fetchall("SELECT item_code,quantity FROM inventory WHERE user_id=? AND namespace='game' AND quantity>0",(uid,)); text="<b>🎒 انبار</b>\n"+("\n".join(f"{r['item_code']}: {r['quantity']}" for r in rows) or "خالی")
 elif action=="shop":
  rows=await db.fetchall("SELECT code,name,price FROM items"); text="<b>🛒 فروشگاه</b>\n"+"\n".join(f"{r['code']} — {r['name']}: {r['price']}" for r in rows)
 elif action=="quest":
  rows=await db.fetchall("SELECT title,reward_coins FROM quests WHERE active=1"); text="<b>🎯 ماموریت‌ها</b>\n"+"\n".join(f"{r['title']} — {r['reward_coins']} سکه" for r in rows)
 else:
  rows=await db.fetchall("SELECT user_id,level,xp FROM game_profiles ORDER BY level DESC,xp DESC LIMIT 10"); text="<b>🏆 برترین‌ها</b>\n"+"\n".join(f"{i}. <code>{r['user_id']}</code> L{r['level']}" for i,r in enumerate(rows,1))
 await call.message.edit_text(text,reply_markup=keyboard()); await call.answer()
