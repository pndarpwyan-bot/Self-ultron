"""Idempotent SQLite migrations."""
from __future__ import annotations

MIGRATIONS: list[tuple[int, str]] = [
    (1, """
    CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS users (
      user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT NOT NULL DEFAULT '', language TEXT NOT NULL DEFAULT 'fa',
      is_blocked INTEGER NOT NULL DEFAULT 0, is_allowed INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS settings (
      user_id INTEGER NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(user_id,key),
      FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY, added_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS chats (
      chat_id INTEGER PRIMARY KEY, title TEXT, chat_type TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS filters (
      id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL, chat_id INTEGER NOT NULL,
      word TEXT NOT NULL, action TEXT NOT NULL DEFAULT 'delete', enabled INTEGER NOT NULL DEFAULT 1,
      UNIQUE(chat_id,word)
    );
    CREATE TABLE IF NOT EXISTS autoreplies (
      id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL, chat_id INTEGER NOT NULL DEFAULT 0,
      scope TEXT NOT NULL DEFAULT 'all', trigger TEXT NOT NULL, response_type TEXT NOT NULL DEFAULT 'text',
      response TEXT NOT NULL, file_id TEXT, enabled INTEGER NOT NULL DEFAULT 1,
      UNIQUE(owner_id,chat_id,trigger)
    );
    CREATE TABLE IF NOT EXISTS content (
      id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL, category TEXT NOT NULL DEFAULT 'general',
      title TEXT NOT NULL, content_type TEXT NOT NULL, body TEXT, file_id TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS scheduled_jobs (
      id TEXT PRIMARY KEY, owner_id INTEGER NOT NULL, chat_id INTEGER NOT NULL, job_type TEXT NOT NULL,
      schedule_type TEXT NOT NULL, schedule_value TEXT NOT NULL, payload TEXT NOT NULL,
      enabled INTEGER NOT NULL DEFAULT 1, next_run TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS statistics (
      key TEXT PRIMARY KEY, value INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS user_activity (
      user_id INTEGER NOT NULL, day TEXT NOT NULL, messages INTEGER NOT NULL DEFAULT 0,
      commands INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(user_id,day)
    );
    CREATE TABLE IF NOT EXISTS warnings (
      chat_id INTEGER NOT NULL, user_id INTEGER NOT NULL, count INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(chat_id,user_id)
    );
    CREATE TABLE IF NOT EXISTS chat_settings (
      chat_id INTEGER NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(chat_id,key)
    );
    CREATE TABLE IF NOT EXISTS game_profiles (
      user_id INTEGER PRIMARY KEY, xp INTEGER NOT NULL DEFAULT 0, level INTEGER NOT NULL DEFAULT 1,
      coins INTEGER NOT NULL DEFAULT 100, daily_claimed_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS items (
      id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
      price INTEGER NOT NULL, sell_price INTEGER NOT NULL, metadata TEXT NOT NULL DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS inventory (
      user_id INTEGER NOT NULL, item_code TEXT NOT NULL, quantity INTEGER NOT NULL DEFAULT 0,
      namespace TEXT NOT NULL DEFAULT 'game', PRIMARY KEY(user_id,item_code,namespace)
    );
    CREATE TABLE IF NOT EXISTS quests (
      id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
      target INTEGER NOT NULL, reward_coins INTEGER NOT NULL, reward_xp INTEGER NOT NULL, active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS user_quests (
      user_id INTEGER NOT NULL, quest_code TEXT NOT NULL, progress INTEGER NOT NULL DEFAULT 0,
      claimed INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(user_id,quest_code)
    );
    CREATE TABLE IF NOT EXISTS rewards (
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, kind TEXT NOT NULL,
      amount INTEGER NOT NULL, claimed_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS cooldowns (
      user_id INTEGER NOT NULL, action TEXT NOT NULL, available_at TEXT NOT NULL, PRIMARY KEY(user_id,action)
    );
    CREATE TABLE IF NOT EXISTS auto_tasks (
      user_id INTEGER NOT NULL, task_type TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,
      interval_seconds INTEGER NOT NULL, next_run TEXT NOT NULL, metadata TEXT NOT NULL DEFAULT '{}',
      PRIMARY KEY(user_id,task_type)
    );
    CREATE TABLE IF NOT EXISTS meow_profiles (
      user_id INTEGER PRIMARY KEY, balance INTEGER NOT NULL DEFAULT 250, xp INTEGER NOT NULL DEFAULT 0,
      level INTEGER NOT NULL DEFAULT 1, notifications INTEGER NOT NULL DEFAULT 1,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS fish (
      code TEXT PRIMARY KEY, name TEXT NOT NULL, rarity TEXT NOT NULL, value INTEGER NOT NULL,
      min_level INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS recipes (
      code TEXT PRIMARY KEY, name TEXT NOT NULL, input_item TEXT NOT NULL, input_quantity INTEGER NOT NULL,
      output_item TEXT NOT NULL, output_quantity INTEGER NOT NULL, min_level INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS factory (
      user_id INTEGER PRIMARY KEY, level INTEGER NOT NULL DEFAULT 1, slots INTEGER NOT NULL DEFAULT 1,
      produced INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS transactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, namespace TEXT NOT NULL,
      kind TEXT NOT NULL, amount INTEGER NOT NULL, description TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_autoreplies_trigger ON autoreplies(trigger,enabled);
    CREATE INDEX IF NOT EXISTS idx_filters_chat ON filters(chat_id,enabled);
    CREATE INDEX IF NOT EXISTS idx_jobs_enabled ON scheduled_jobs(enabled);
    CREATE INDEX IF NOT EXISTS idx_auto_next ON auto_tasks(enabled,next_run);
    """),
    (2, """
    CREATE TABLE IF NOT EXISTS forward_rules (
      id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL, source_chat_id INTEGER NOT NULL,
      destination_chat_id INTEGER NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(owner_id,source_chat_id,destination_chat_id)
    );
    CREATE TABLE IF NOT EXISTS reactions (
      chat_id INTEGER PRIMARY KEY, emoji TEXT NOT NULL DEFAULT '❤', enabled INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS game_stats (
      user_id INTEGER NOT NULL, key TEXT NOT NULL, value INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(user_id,key)
    );
    """)
]
