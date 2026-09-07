"""Async SQLite gateway with serialized writes and migration support."""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Iterable

import aiosqlite

from database.migrations import MIGRATIONS


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.connection: aiosqlite.Connection | None = None
        self._write_lock = asyncio.Lock()

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = await aiosqlite.connect(self.path)
        self.connection.row_factory = aiosqlite.Row
        await self.connection.execute("PRAGMA foreign_keys=ON")
        await self.connection.execute("PRAGMA journal_mode=WAL")
        await self.connection.execute("PRAGMA busy_timeout=5000")
        await self.migrate()
        await self.seed()

    async def close(self) -> None:
        if self.connection:
            await self.connection.close()
            self.connection = None

    def _conn(self) -> aiosqlite.Connection:
        if not self.connection:
            raise RuntimeError("Database is not connected")
        return self.connection

    async def migrate(self) -> None:
        conn = self._conn()
        await conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        row = await self.fetchone("SELECT COALESCE(MAX(version),0) AS version FROM schema_version")
        current = int(row["version"]) if row else 0
        for version, script in MIGRATIONS:
            if version <= current:
                continue
            await conn.executescript(script)
            await conn.execute("INSERT INTO schema_version(version) VALUES (?)", (version,))
            await conn.commit()

    async def seed(self) -> None:
        fish = [("sardine", "ساردین", "معمولی", 15, 1), ("salmon", "سالمون", "کمیاب", 45, 2),
                ("tuna", "تن", "نادر", 90, 4), ("goldfish", "ماهی طلایی", "افسانه‌ای", 350, 8)]
        await self.executemany("INSERT OR IGNORE INTO fish(code,name,rarity,value,min_level) VALUES(?,?,?,?,?)", fish)
        items = [("rod", "چوب ماهیگیری", 150, 75, '{}'), ("bait", "طعمه", 20, 10, '{}'),
                 ("factory_part", "قطعه کارخانه", 300, 150, '{}')]
        await self.executemany("INSERT OR IGNORE INTO items(code,name,price,sell_price,metadata) VALUES(?,?,?,?,?)", items)
        await self.execute("INSERT OR IGNORE INTO quests(code,title,target,reward_coins,reward_xp) VALUES(?,?,?,?,?)",
                           ("fish_10", "صید ۱۰ ماهی", 10, 200, 80))
        await self.execute("INSERT OR IGNORE INTO recipes(code,name,input_item,input_quantity,output_item,output_quantity,min_level) VALUES(?,?,?,?,?,?,?)",
                           ("grilled_fish", "ماهی کبابی", "sardine", 2, "grilled_fish", 1, 1))

    async def execute(self, sql: str, params: Iterable[Any] = ()) -> int:
        async with self._write_lock:
            cursor = await self._conn().execute(sql, tuple(params))
            await self._conn().commit()
            return cursor.lastrowid or 0

    async def executemany(self, sql: str, rows: Iterable[Iterable[Any]]) -> None:
        async with self._write_lock:
            await self._conn().executemany(sql, rows)
            await self._conn().commit()

    async def fetchone(self, sql: str, params: Iterable[Any] = ()) -> aiosqlite.Row | None:
        cursor = await self._conn().execute(sql, tuple(params))
        return await cursor.fetchone()

    async def fetchall(self, sql: str, params: Iterable[Any] = ()) -> list[aiosqlite.Row]:
        cursor = await self._conn().execute(sql, tuple(params))
        return list(await cursor.fetchall())

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[aiosqlite.Connection]:
        async with self._write_lock:
            conn = self._conn()
            await conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise

    async def upsert_user(self, user_id: int, username: str | None, full_name: str) -> None:
        await self.execute(
            """INSERT INTO users(user_id,username,full_name) VALUES(?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,full_name=excluded.full_name,last_seen=CURRENT_TIMESTAMP""",
            (user_id, username, full_name[:128]),
        )

    async def upsert_chat(self, chat_id: int, title: str | None, chat_type: str) -> None:
        await self.execute(
            """INSERT INTO chats(chat_id,title,chat_type) VALUES(?,?,?)
            ON CONFLICT(chat_id) DO UPDATE SET title=excluded.title,chat_type=excluded.chat_type,active=1""",
            (chat_id, (title or "")[:128], chat_type),
        )

    async def get_setting(self, user_id: int, key: str, default: str = "") -> str:
        row = await self.fetchone("SELECT value FROM settings WHERE user_id=? AND key=?", (user_id, key))
        return str(row["value"]) if row else default

    async def set_setting(self, user_id: int, key: str, value: str) -> None:
        await self.execute(
            "INSERT INTO settings(user_id,key,value) VALUES(?,?,?) ON CONFLICT(user_id,key) DO UPDATE SET value=excluded.value",
            (user_id, key, value),
        )

    async def increment_stat(self, key: str, amount: int = 1) -> None:
        await self.execute(
            "INSERT INTO statistics(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=value+excluded.value",
            (key, amount),
        )

    async def record_activity(self, user_id: int, command: bool = False) -> None:
        await self.execute(
            """INSERT INTO user_activity(user_id,day,messages,commands) VALUES(?,date('now'),1,?)
            ON CONFLICT(user_id,day) DO UPDATE SET messages=messages+1,commands=commands+excluded.commands""",
            (user_id, int(command)),
        )

    async def ensure_game_profiles(self, user_id: int) -> None:
        await self.execute("INSERT OR IGNORE INTO game_profiles(user_id) VALUES(?)", (user_id,))
        await self.execute("INSERT OR IGNORE INTO meow_profiles(user_id) VALUES(?)", (user_id,))
        await self.execute("INSERT OR IGNORE INTO factory(user_id) VALUES(?)", (user_id,))

    async def add_inventory(self, user_id: int, item: str, amount: int, namespace: str = "game") -> None:
        await self.execute(
            """INSERT INTO inventory(user_id,item_code,quantity,namespace) VALUES(?,?,?,?)
            ON CONFLICT(user_id,item_code,namespace) DO UPDATE SET quantity=MAX(0,quantity+excluded.quantity)""",
            (user_id, item, amount, namespace),
        )

    @staticmethod
    def json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
