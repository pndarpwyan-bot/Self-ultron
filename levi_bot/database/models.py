"""Typed records shared by database and plugins."""
from dataclasses import dataclass


@dataclass(slots=True)
class UserRecord:
    user_id: int
    username: str | None
    full_name: str
    language: str = "fa"
    is_blocked: bool = False


@dataclass(slots=True)
class GameProfile:
    user_id: int
    xp: int
    level: int
    coins: int


@dataclass(slots=True)
class MeowProfile:
    user_id: int
    balance: int
    xp: int
    level: int
    notifications: bool
