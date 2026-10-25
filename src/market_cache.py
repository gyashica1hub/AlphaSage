"""Persistent local cache for quotes and historical OHLC data."""

import json
from datetime import UTC, datetime

from src.db.sqlite import get_connection


def _now() -> datetime:
    return datetime.now(UTC)


class MarketCache:
    def get_quote(self, symbol: str, max_age_seconds: int) -> dict | None:
        with get_connection() as connection:
            row = connection.execute("SELECT payload, fetched_at FROM market_quotes WHERE symbol = ?", (symbol,)).fetchone()
        if not row:
            return None
        fetched_at = datetime.fromisoformat(row["fetched_at"])
        if (_now() - fetched_at).total_seconds() > max_age_seconds:
            return None
        return {**json.loads(row["payload"]), "cache": "persistent-hit"}

    def put_quote(self, symbol: str, payload: dict) -> None:
        fetched_at = payload.get("fetched_at") or _now().isoformat()
        with get_connection() as connection:
            connection.execute(
                """INSERT INTO market_quotes(symbol, payload, fetched_at) VALUES (?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET payload = excluded.payload, fetched_at = excluded.fetched_at""",
                (symbol, json.dumps(payload), fetched_at),
            )

    def clear(self, symbol: str) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM market_quotes WHERE symbol = ?", (symbol,))
            connection.execute("DELETE FROM market_history WHERE symbol = ?", (symbol,))

    def get_history(self, symbol: str, max_age_seconds: int) -> list[dict] | None:
        with get_connection() as connection:
            latest = connection.execute("SELECT MAX(fetched_at) AS fetched_at FROM market_history WHERE symbol = ?", (symbol,)).fetchone()
            if not latest or not latest["fetched_at"]:
                return None
            fetched_at = datetime.fromisoformat(latest["fetched_at"])
            if (_now() - fetched_at).total_seconds() > max_age_seconds:
                return None
            rows = connection.execute("SELECT date, open, high, low, close, volume FROM market_history WHERE symbol = ? ORDER BY date", (symbol,)).fetchall()
        return [dict(row) for row in rows]

    def put_history(self, symbol: str, points: list[dict]) -> None:
        fetched_at = _now().isoformat()
        with get_connection() as connection:
            connection.execute("DELETE FROM market_history WHERE symbol = ?", (symbol,))
            connection.executemany(
                "INSERT INTO market_history(symbol, date, open, high, low, close, volume, fetched_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [(symbol, point["date"], point.get("open"), point.get("high"), point.get("low"), point["close"], point.get("volume"), fetched_at) for point in points],
            )
