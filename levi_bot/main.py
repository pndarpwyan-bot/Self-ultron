"""Levi Bot command-line entry point."""
from __future__ import annotations

import asyncio
from pathlib import Path

from config import BASE_DIR, load_settings
from core.bot import run_bot
from core.logger import setup_logging


def main() -> None:
    settings = load_settings(require_token=True)
    setup_logging(settings.log_level, Path(BASE_DIR) / "data")
    try:
        asyncio.run(run_bot(settings))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
