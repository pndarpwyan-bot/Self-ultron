"""Environment-backed application configuration."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    admin_id: int | None
    ai_api_key: str | None
    ai_base_url: str
    ai_model: str
    translation_api_key: str | None
    translation_api_url: str
    currency_api_url: str
    database_path: Path
    log_level: str


def load_settings(*, require_token: bool = True) -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if require_token and not token:
        raise RuntimeError(
            "BOT_TOKEN تنظیم نشده است. فایل .env را از روی .env.example بسازید "
            "و BOT_TOKEN=... را در آن قرار دهید."
        )
    raw_admin = os.getenv("ADMIN_ID", "").strip()
    try:
        admin_id = int(raw_admin) if raw_admin else None
    except ValueError as exc:
        raise RuntimeError("ADMIN_ID باید یک شناسه عددی تلگرام باشد.") from exc
    db_value = os.getenv("DATABASE_PATH", "data/levi.sqlite3")
    db_path = Path(db_value)
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path
    return Settings(
        bot_token=token,
        admin_id=admin_id,
        ai_api_key=os.getenv("AI_API_KEY") or None,
        ai_base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1"),
        ai_model=os.getenv("AI_MODEL", "gpt-4o-mini"),
        translation_api_key=os.getenv("TRANSLATION_API_KEY") or None,
        translation_api_url=os.getenv("TRANSLATION_API_URL", "https://api.mymemory.translated.net/get"),
        currency_api_url=os.getenv("CURRENCY_API_URL", "https://api.frankfurter.app"),
        database_path=db_path,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
