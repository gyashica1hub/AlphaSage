from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.models import Base, Note, Portfolio, Transaction, User, Watchlist
from src.repositories.workspace import WorkspaceRepository


def test_workspace_repository_scopes_records_to_user():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.add_all([
            User(id="a", email="a@x.test", created_at=now, updated_at=now),
            User(id="b", email="b@x.test", created_at=now, updated_at=now),
            Portfolio(id="pa", user_id="a", name="A", created_at=now, updated_at=now),
            Portfolio(id="pb", user_id="b", name="B", created_at=now, updated_at=now),
            Watchlist(id="wa", user_id="a", name="A watchlist", created_at=now, updated_at=now),
            Watchlist(id="wb", user_id="b", name="B watchlist", created_at=now, updated_at=now),
            Note(id="na", user_id="a", body="private", created_at=now, updated_at=now),
            Note(id="nb", user_id="b", body="private", created_at=now, updated_at=now),
            Transaction(id="ta", portfolio_id="pa", symbol="AAA.NS", side="BUY", quantity=1, price=10, executed_at=now),
        ])
        session.commit()
        repository = WorkspaceRepository(session)
        assert [item.id for item in repository.watchlists_for_user("a")] == ["wa"]
        assert [item.id for item in repository.notes_for_user("a")] == ["na"]
        assert repository.transactions_for_user("pa", "b") == []
        assert [item.id for item in repository.transactions_for_user("pa", "a")] == ["ta"]
