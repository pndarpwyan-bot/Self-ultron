from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from config import Settings
from core.rate_limit import RateLimiter
from services.ai import AIService,AIServiceError
from services.translate import TranslationService

router=Router(name="ai")

@router.message(Command("ai"))
async def ai(message:Message,settings:Settings,rate_limiter:RateLimiter)->None:
 if not await rate_limiter.allow(f"ai:{message.from_user.id}"): await message.answer("درخواست‌ها زیاد است؛ کمی صبر کنید."); return
 text=(message.text or "").partition(" ")[2]
 if not text: await message.answer("/ai پرسش\n/ai summarize متن\n/ai translate متن"); return
 system="You are a concise helpful assistant. Reply in the user's language."
 if text.startswith("summarize "): system="Summarize accurately and concisely in the source language."; text=text[10:]
 elif text.startswith("translate "): system="Translate the text to Persian unless another target is explicitly specified. Output only translation."; text=text[10:]
 try: answer=await AIService(settings.ai_api_key,settings.ai_base_url,settings.ai_model).ask(text,system)
 except AIServiceError as e: await message.answer(f"AI در دسترس نیست: {e}"); return
 await message.answer(answer[:4000])

@router.message(Command("translate"))
async def translate(message:Message,settings:Settings)->None:
 p=(message.text or "").split(maxsplit=2)
 if len(p)<3: await message.answer("/translate en متن"); return
 try: result=await TranslationService(settings.translation_api_url,settings.translation_api_key).translate(p[2],p[1])
 except Exception as e: await message.answer(f"ترجمه انجام نشد: {e}"); return
 await message.answer(result[:4000])
