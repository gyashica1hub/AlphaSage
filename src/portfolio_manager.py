"""SQLite-backed portfolio operations for the current demo user.

The demo user is temporary. Authentication will replace this fixed identity,
but the dashboard already uses the same user_id/portfolio_id ownership model.
"""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from src.db.sqlite import get_connection, initialize_database

DEMO_USER_ID = "demo-user"
DEMO_EMAIL = "demo@alphasage.local"
DEMO_PORTFOLIO_NAME = "Personal Portfolio"
SEED_FILE = Path(__file__).resolve().parents[1] / "data" / "mock_portfolio.json"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _ensure_demo_portfolio(user_id: str = DEMO_USER_ID) -> str:
    initialize_database()
    now = _now()

    with get_connection() as connection:
        connection.execute(
            """INSERT OR IGNORE INTO users
               (id, email, display_name, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, f"{user_id}@alphasage.local", "Demo User" if user_id == DEMO_USER_ID else "AlphaSage User", now, now),
        )

        portfolio = connection.execute(
            "SELECT id FROM portfolios WHERE user_id = ? LIMIT 1",
            (user_id,),
        ).fetchone()

        if portfolio:
            portfolio_id = portfolio["id"]
        else:
            portfolio_id = str(uuid.uuid4())
            connection.execute(
                """INSERT INTO portfolios
                   (id, user_id, name, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (portfolio_id, user_id, DEMO_PORTFOLIO_NAME, now, now),
            )

        position_count = connection.execute(
            "SELECT COUNT(*) AS count FROM portfolio_positions WHERE portfolio_id = ?",
            (portfolio_id,),
        ).fetchone()["count"]

        if position_count == 0 and SEED_FILE.exists() and user_id == DEMO_USER_ID:
            seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
            for holding in seed.get("holdings", []):
                connection.execute(
                    """INSERT OR IGNORE INTO portfolio_positions
                       (id, portfolio_id, symbol, name, quantity,
                        average_buy_price, sector, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(uuid.uuid4()),
                        portfolio_id,
                        holding["symbol"],
                        holding.get("name", holding["symbol"]),
                        holding["quantity"],
                        holding["avg_buy_price"],
                        holding.get("sector", "Other"),
                        now,
                        now,
                    ),
                )

    return portfolio_id


def _holdings(portfolio_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """SELECT symbol, name, quantity, average_buy_price,
                      sector, created_at
               FROM portfolio_positions
               WHERE portfolio_id = ?
               ORDER BY symbol""",
            (portfolio_id,),
        ).fetchall()

    return [
        {
            "symbol": row["symbol"],
            "name": row["name"],
            "quantity": row["quantity"],
            "avg_buy_price": row["average_buy_price"],
            "buy_date": row["created_at"][:10],
            "sector": row["sector"] or "Other",
        }
        for row in rows
    ]


def load_portfolio_raw(user_id: str = DEMO_USER_ID) -> dict:
    """Return the legacy dashboard shape, backed by SQLite."""
    portfolio_id = _ensure_demo_portfolio(user_id)
    return {
        "user": "Demo User" if user_id == DEMO_USER_ID else "AlphaSage User",
        "broker": "SQLite demo portfolio",
        "portfolio_id": portfolio_id,
        "holdings": _holdings(portfolio_id),
    }


def save_portfolio_raw(data: dict) -> None:
    """Deprecated compatibility method; direct JSON writes are disabled."""
    raise RuntimeError("Direct portfolio file writes are disabled; use add_stock/remove_stock")


def add_stock(
    symbol: str,
    name: str,
    quantity: float,
    avg_buy_price: float,
    buy_date: str,
    sector: str = "Other",
    user_id: str = DEMO_USER_ID,
) -> bool:
    portfolio_id = _ensure_demo_portfolio(user_id)
    symbol = symbol.upper().strip()
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol = symbol + ".NS"

    now = _now()
    with get_connection() as connection:
        existing = connection.execute(
            """SELECT quantity, average_buy_price
               FROM portfolio_positions
               WHERE portfolio_id = ? AND symbol = ?""",
            (portfolio_id, symbol),
        ).fetchone()

        if existing:
            old_quantity = existing["quantity"]
            new_quantity = old_quantity + quantity
            new_average = (
                (old_quantity * existing["average_buy_price"])
                + (quantity * avg_buy_price)
            ) / new_quantity
            connection.execute(
                """UPDATE portfolio_positions
                   SET quantity = ?, average_buy_price = ?, updated_at = ?
                   WHERE portfolio_id = ? AND symbol = ?""",
                (new_quantity, round(new_average, 2), now, portfolio_id, symbol),
            )
        else:
            connection.execute(
                """INSERT INTO portfolio_positions
                   (id, portfolio_id, symbol, name, quantity,
                    average_buy_price, sector, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    portfolio_id,
                    symbol,
                    name or symbol.replace(".NS", "").replace(".BO", ""),
                    quantity,
                    avg_buy_price,
                    sector,
                    now,
                    now,
                ),
            )

    return True


def remove_stock(symbol: str, user_id: str = DEMO_USER_ID) -> bool:
    portfolio_id = _ensure_demo_portfolio(user_id)
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM portfolio_positions WHERE portfolio_id = ? AND symbol = ?",
            (portfolio_id, symbol),
        )
    return True


def get_all_symbols() -> list[tuple[str, str]]:
    data = load_portfolio_raw()
    return [(holding["symbol"], holding["name"]) for holding in data["holdings"]]

