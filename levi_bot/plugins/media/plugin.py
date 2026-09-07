from aiogram import Bot,Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile,Message
from config import Settings
from services.image import image_info,resize_image
from services.stt import speech_to_text
from services.tts import text_to_speech
router=Router(name="media")
async def download_reply(message:Message,bot:Bot)->bytes:
 src=message.reply_to_message
 if not src: raise ValueError("دستور را روی رسانه Reply کنید.")
 obj=src.photo[-1] if src.photo else (src.voice or src.audio or src.document)
 if not obj: raise ValueError("رسانه مناسب نیست.")
 stream=await bot.download(obj); return stream.read()
@router.message(Command("tts"))
async def tts(message:Message)->None:
 text=(message.text or "").partition(" ")[2]
 try: data=await text_to_speech(text)
 except Exception as e: await message.answer(f"تبدیل انجام نشد: {e}"); return
 await message.answer_voice(BufferedInputFile(data.read(),filename="speech.mp3"))
@router.message(Command("stt"))
async def stt(message:Message,bot:Bot,settings:Settings)->None:
 try: text=await speech_to_text(await download_reply(message,bot),settings.ai_api_key,settings.ai_base_url)
 except Exception as e: await message.answer(f"تبدیل انجام نشد: {e}"); return
 await message.answer(text or "متنی تشخیص داده نشد.")
@router.message(Command("imageinfo"))
async def info(message:Message,bot:Bot)->None:
 try: data=await image_info(await download_reply(message,bot))
 except Exception as e: await message.answer(f"خطا: {e}"); return
 await message.answer("\n".join(f"{k}: {v}" for k,v in data.items()))
@router.message(Command("resize"))
async def resize(message:Message,bot:Bot)->None:
 try:
  _,w,h=(message.text or "").split(); image=await resize_image(await download_reply(message,bot),int(w),int(h))
 except Exception as e: await message.answer(f"/resize WIDTH HEIGHT (روی عکس Reply)\nخطا: {e}"); return
 await message.answer_photo(BufferedInputFile(image.read(),filename="resized.jpg"))
