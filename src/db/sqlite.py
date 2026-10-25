"""Small SQLite foundation used by local development and tests."""

import sqlite3
from pathlib import Path
from typing import Iterator

from src.config import settings


def _database_path() -> Path:
    prefix = "sqlite:///"
    if not settings.database_url.startswith(prefix):
        raise ValueError("Local foundation currently supports sqlite:/// URLs only")
    return Path(settings.database_url[len(prefix):])


def get_connection() -> sqlite3.Connection:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    with get_connection() as connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        columns = {row[1] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
        if "email_verified" not in columns:
            connection.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0")
            connection.execute("UPDATE users SET email_verified = 1")
        alert_columns = {row[1] for row in connection.execute("PRAGMA table_info(alerts)").fetchall()}
        if "cooldown_minutes" not in alert_columns:
            connection.execute("ALTER TABLE alerts ADD COLUMN cooldown_minutes INTEGER NOT NULL DEFAULT 60")
        if "last_triggered_at" not in alert_columns:
            connection.execute("ALTER TABLE alerts ADD COLUMN last_triggered_at TEXT")


def connection() -> Iterator[sqlite3.Connection]:
    database = get_connection()
    try:
        yield database
    finally:
        database.close()
