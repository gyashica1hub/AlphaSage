"""Import the existing demo JSON portfolio into the local database."""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from src.db.sqlite import get_connection, initialize_database


def import_demo_portfolio(
    portfolio_path: str = "data/mock_portfolio.json",
    user_id: str = "demo-user",
) -> None:
    initialize_database()
    payload = json.loads(Path(portfolio_path).read_text(encoding="utf-8"))
    now = datetime.now(UTC).isoformat()
    portfolio_id = str(uuid.uuid4())

    with get_connection() as connection:
        connection.execute(
            """INSERT OR IGNORE INTO users
               (id, email, display_name, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, "demo@stocksense.local", payload.get("user", "Demo User"), now, now),
        )
        existing = connection.execute(
            "SELECT id FROM portfolios WHERE user_id = ? LIMIT 1", (user_id,)
        ).fetchone()
        if existing:
            portfolio_id = existing["id"]
        else:
            connection.execute(
                "INSERT INTO portfolios (id, user_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (portfolio_id, user_id, "Imported Portfolio", now, now),
            )

        for holding in payload.get("holdings", []):
            connection.execute(
                """INSERT INTO portfolio_positions
                   (id, portfolio_id, symbol, name, quantity, average_buy_price, sector, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(portfolio_id, symbol) DO UPDATE SET
                     name=excluded.name, quantity=excluded.quantity,
                     average_buy_price=excluded.average_buy_price,
                     sector=excluded.sector, updated_at=excluded.updated_at""",
                (
                    str(uuid.uuid4()), portfolio_id, holding["symbol"], holding.get("name", holding["symbol"]),
                    holding["quantity"], holding["avg_buy_price"], holding.get("sector"), now, now,
                ),
            )


if __name__ == "__main__":
    import_demo_portfolio()
    print("Demo portfolio imported into data/stocksense.db")
