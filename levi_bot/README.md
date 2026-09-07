# Levi Bot

ربات چندمنظوره و ماژولار Telegram Bot API با Python و aiogram. این پروژه مستقل است، از اکانت شخصی/Userbot استفاده نمی‌کند و تمام داده‌های نسخه اولیه را در SQLite نگه می‌دارد.

## قابلیت‌ها

- پنل Inline فارسی، پروفایل، تنظیمات، آمار، پنل مدیر، Blocklist و Allowlist
- پاسخ خودکار، فیلتر کلمه، Reaction، Auto Forward، محتوای ذخیره‌شده و زمان‌بندی پایدار
- مدیریت گروه: ban/unban/kick/mute/unmute/warn/pin/rules، Anti-Link و Tag کنترل‌شده
- AI، ترجمه، TTS/STT، اطلاعات/Resize تصویر، نرخ ارز، فونت Unicode و ماشین‌حساب AST امن
- Game Engine با XP، Level، Coin، Inventory، Shop، Quest، Daily Reward و Leaderboard
- Meow Game چندکاربره با ماهیگیری، آشپزی، کارخانه، فروشگاه، مأموریت و Auto Taskهای پایدار
- جداسازی خطای Plugin: خطای import یک افزونه ثبت می‌شود و مانع اجرای سایر افزونه‌ها نیست.

## پیش‌نیاز

- Python 3.12 یا جدیدتر
- توکن ربات از [@BotFather](https://t.me/BotFather)
- برای مدیریت گروه، ربات باید مجوز لازم را در همان گروه داشته باشد.

## نصب در Termux

```bash
pkg update -y && pkg upgrade -y
pkg install -y python git clang libjpeg-turbo
cd ~
git clone https://github.com/pndarpwyan-bot/Self-ultron.git
cd Self-ultron/levi_bot
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
cp .env.example .env
nano .env
python main.py
```

اگر نصب Pillow روی دستگاه خاصی خطا داد:

```bash
pkg install -y libjpeg-turbo libpng freetype
pip install --no-cache-dir Pillow
```

## نصب در Linux / VPS

Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
# در صورت قدیمی بودن Python سیستم، Python 3.12 را از مخزن رسمی توزیع نصب کنید.
git clone https://github.com/pndarpwyan-bot/Self-ultron.git
cd Self-ultron/levi_bot
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
nano .env
python main.py
```

برای اجرای پایدار، نمونه systemd (مسیرها را تغییر دهید):

```ini
[Unit]
Description=Levi Telegram Bot
After=network-online.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/Self-ultron/levi_bot
ExecStart=/opt/Self-ultron/levi_bot/.venv/bin/python main.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

## تنظیم `.env`

```bash
cp .env.example .env
```

حداقل مقدار ضروری:

```dotenv
BOT_TOKEN=123456789:token_from_botfather
ADMIN_ID=123456789
```

گزینه‌های سرویس:

```dotenv
AI_API_KEY=
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
TRANSLATION_API_KEY=
TRANSLATION_API_URL=https://api.mymemory.translated.net/get
CURRENCY_API_URL=https://api.frankfurter.app
DATABASE_PATH=data/levi.sqlite3
LOG_LEVEL=INFO
DISABLED_PLUGINS=
```

`BOT_TOKEN` در Source قرار ندارد و نبود آن هنگام Startup یک خطای واضح ایجاد می‌کند. بدون `AI_API_KEY` فقط AI و STT پیام «غیرفعال» می‌دهند و ربات Crash نمی‌کند. فایل `.env` توسط Git نادیده گرفته می‌شود.

## اجرا

```bash
cd levi_bot
source .venv/bin/activate
python main.py
```

ربات از Long Polling استفاده می‌کند. برای توقف `Ctrl+C` بزنید.

## دستورات

### عمومی و مدیریت حساب

- `/start`, `/help`, `/ping`, `/alive`, `/stats`, `/profile`
- `/settings language fa|en`
- `/settings feature NAME on|off`
- `/admin`, `/adminhelp`
- مالک: `/block ID`, `/unblock ID`, `/allow ID`, `/disallow ID`, `/addadmin ID`, `/deladmin ID`

### پاسخ، فیلتر، Reaction و Forward

- `/autoreply add trigger | response`, `/autoreply list`, `/autoreply del ID`, `/autoreply toggle ID`؛ برای پاسخ رسانه‌ای، دستور Add را روی Photo/Video/Document ریپلای کنید.
- `/filter add WORD [delete|warn|mute]`, `/filter list`, `/filter del ID`, `/filter toggle ID`
- `/reaction on ❤️`, `/reaction off`
- `/forward add SOURCE_CHAT_ID DEST_CHAT_ID`, `/forward list`, `/forward del ID`, `/forward stop`

### زمان‌بندی و محتوا

- `/schedule once 2026-12-31T20:00:00+00:00 متن`
- `/schedule daily 12:30 متن`
- `/schedule weekly mon@12:30 متن`
- `/schedule list`, `/schedule del ID`, `/schedule pause ID`, `/schedule resume ID`
- `/content save CATEGORY TITLE | TEXT`؛ برای رسانه روی Photo/Video/Document پاسخ دهید.
- `/content list [CATEGORY]`, `/content send ID`, `/content del ID`

### سرویس‌ها و ابزارها

- `/font text`
- `/translate en text`
- `/ai question`, `/ai summarize text`, `/ai translate text`
- `/tts text`, `/stt` روی Voice، `/imageinfo` روی عکس، `/resize WIDTH HEIGHT` روی عکس
- `/currency USD EUR [AMOUNT]`
- `/calc (2+3)*4`, `/percent 20 150`

### گروه

- روی پیام عضو: `/ban`, `/unban`, `/kick`, `/mute`, `/unmute`, `/warn`, `/unwarn`
- روی پیام: `/pin`
- `/setrules TEXT`, `/rules`
- `/tag TEXT`, `/tagstop`
- `/antilink on|off`, `/antispam on|off`
- `/welcome TEXT|off`, `/goodbye TEXT|off`؛ متغیرهای `{name}` و `{id}` پشتیبانی می‌شوند.
- عملیات مدیریتی فقط با مجوز رسمی Telegram انجام می‌شود.

### بازی عمومی

- `/game`, `/daily`, `/inventory`, `/shop`, `/buy CODE [QTY]`, `/sell CODE [QTY]`
- `/quest`, `/leaderboard`

### Meow Game

- `/meow`, `/meow profile`, `/meow balance`, `/meow inventory`, `/meow fish`
- `/meow cook`, `/meow factory`, `/meow shop`, `/meow buy CODE [QTY]`, `/meow sell CODE [QTY]`
- `/meow quest`, `/meow claim`, `/meow level`, `/meow stats`, `/meow leaderboard`
- `/meow autofish on|off`, `/meow autocook on|off`, `/meow autofactory on|off`
- `/meow autosell on|off`, `/meow autoquest on|off`, `/meow auto`, `/meow stop [TASK]`

## Pluginها

هر Plugin در `plugins/<name>/plugin.py` یک `router` مستقل صادر می‌کند. Loader خطاهای import را جداگانه Log می‌کند. برای غیرفعال‌سازی بدون تغییر کد:

```dotenv
DISABLED_PLUGINS=ai,media,forward
```

نام‌های معتبر: `profile, autoreply, filter, reaction, scheduler, forward, content, fonts, media, groups, ai, tools, games, meow`.

برای افزودن Plugin، یک `Router` بسازید و مسیر Module را به `PLUGIN_MODULES` در `core/loader.py` اضافه کنید. Handlerها نباید State سراسری mutable یا اتصال SQLite جداگانه بسازند.

## دیتابیس و پایداری

- SQLite در حالت WAL، Foreign Keys و Busy Timeout اجرا می‌شود.
- Writeها با Lock async سریال می‌شوند؛ Queryها پارامتری هستند.
- Migrationهای idempotent در Startup اعمال می‌شوند.
- Jobهای پیام از `scheduled_jobs` و Auto Taskهای بازی از `auto_tasks` بعد از Restart بازیابی می‌شوند.
- Log چرخشی در `data/bot.log` ذخیره می‌شود.

## محدودیت‌های رسمی Telegram Bot API

- Bot نمی‌تواند پیام‌ها را مانند حساب شخصی «Seen» کند یا تاریخچه دلخواه چت را بخواند.
- Forward فقط برای Updateهایی ممکن است که Telegram به Bot تحویل می‌دهد و Bot در مقصد اجازه ارسال دارد.
- Tag همه اعضا ممکن نیست، چون Bot API فهرست کامل اعضای گروه را ارائه نمی‌دهد؛ این پروژه فقط کاربران شناخته‌شده قبلی را با Delay و Batch کوچک Tag می‌کند.
- حذف، Pin، Ban، Restrict و فیلتر فقط با دسترسی ادمین و فقط روی پیام‌ها/کاربران مجاز Telegram انجام می‌شود.
- Reaction تنها در گفتگوها و برای Emojiهای مجاز همان Chat کار می‌کند؛ واکنش/Seen جعلی ساخته نمی‌شود.
- Bot نمی‌تواند محدودیت Privacy Mode یا Rate Limit تلگرام را دور بزند.

## تست

```bash
python -m compileall -q .
python -m unittest discover -s tests -v
```

تست‌ها Config، محاسبه امن، Migration، عملیات Inventory و بارگذاری Pluginها را بررسی می‌کنند و به Token واقعی نیاز ندارند.

## مشکلات رایج

- **`BOT_TOKEN تنظیم نشده است`**: `.env` را کنار `main.py` بسازید، نه در پوشه والد.
- **`Unauthorized`**: توکن اشتباه/لغو شده؛ توکن جدید BotFather را قرار دهید.
- **عملیات گروه انجام نمی‌شود**: Bot و صادرکننده فرمان باید Admin باشند و مجوز Delete/Ban/Restrict/Pin فعال باشد.
- **پیام‌های عادی گروه نمی‌رسند**: Privacy Mode را با BotFather متناسب با نیاز خاموش کنید و قوانین حریم خصوصی را رعایت کنید.
- **AI/STT غیرفعال است**: `AI_API_KEY` و در صورت نیاز `AI_BASE_URL` سازگار را تنظیم کنید.
- **خطای Translation/Currency**: اینترنت، URL Provider و محدودیت سرویس عمومی را بررسی کنید.
- **`database is locked`**: فقط یک Instance را با همان فایل DB اجرا کنید.
- **خطای یک Plugin**: `data/bot.log` را ببینید؛ Loader سایر Pluginها را اجرا نگه می‌دارد.
