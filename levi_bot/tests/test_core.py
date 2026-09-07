from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from config import load_settings
from database.db import Database
from plugins.tools.plugin import calculate


class ConfigTests(unittest.TestCase):
    def test_missing_token_has_clear_error(self) -> None:
        old = os.environ.pop("BOT_TOKEN", None)
        try:
            with self.assertRaisesRegex(RuntimeError, "BOT_TOKEN"):
                load_settings(require_token=True)
        finally:
            if old is not None:
                os.environ["BOT_TOKEN"] = old

    def test_calculator(self) -> None:
        self.assertEqual(calculate("(2+3)*4"), 20)
        self.assertAlmostEqual(calculate("10/4"), 2.5)
        with self.assertRaises(ValueError):
            calculate("__import__('os').system('id')")
        with self.assertRaises(ValueError):
            calculate("2**999")


class DatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "test.sqlite3")
        await self.db.connect()

    async def asyncTearDown(self) -> None:
        await self.db.close()
        self.temp.cleanup()

    async def test_migrations_and_inventory(self) -> None:
        row = await self.db.fetchone("SELECT MAX(version) version FROM schema_version")
        self.assertGreaterEqual(row["version"], 2)
        await self.db.upsert_user(1, "tester", "Test User")
        await self.db.ensure_game_profiles(1)
        await self.db.add_inventory(1, "sardine", 2, "meow")
        await self.db.add_inventory(1, "sardine", -1, "meow")
        item = await self.db.fetchone(
            "SELECT quantity FROM inventory WHERE user_id=1 AND item_code='sardine' AND namespace='meow'"
        )
        self.assertEqual(item["quantity"], 1)

    async def test_parameterized_autoreply(self) -> None:
        await self.db.upsert_user(2, None, "O'Reilly")
        await self.db.execute(
            "INSERT INTO autoreplies(owner_id,chat_id,trigger,response) VALUES(?,?,?,?)",
            (2, 2, "' OR 1=1 --", "safe"),
        )
        rows = await self.db.fetchall("SELECT * FROM autoreplies WHERE owner_id=?", (2,))
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
