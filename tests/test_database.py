import json
import sqlite3

from src.db.import_demo import import_demo_portfolio


def test_demo_portfolio_import(tmp_path, monkeypatch):
    portfolio_file = tmp_path / "portfolio.json"
    portfolio_file.write_text(
        json.dumps({"user": "Test User", "holdings": [{
            "symbol": "TEST.NS", "name": "Test", "quantity": 2,
            "avg_buy_price": 100, "sector": "Technology"
        }]}),
        encoding="utf-8",
    )
    database_file = tmp_path / "stocksense.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_file}")

    # config is intentionally imported once; replace the runtime setting for this isolated test.
    from src import config
    object.__setattr__(config.settings, "database_url", f"sqlite:///{database_file}")
    import_demo_portfolio(str(portfolio_file), user_id="test-user")

    with sqlite3.connect(database_file) as connection:
        assert connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM portfolio_positions").fetchone()[0] == 1
