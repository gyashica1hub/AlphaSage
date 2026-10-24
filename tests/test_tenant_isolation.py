from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.models import Base, Portfolio, PortfolioPosition, User
from src.repositories.portfolio import PortfolioRepository


def test_portfolio_repository_does_not_cross_tenants():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.add_all([
            User(id="user-a", email="a@example.com", created_at=now, updated_at=now),
            User(id="user-b", email="b@example.com", created_at=now, updated_at=now),
            Portfolio(id="portfolio-a", user_id="user-a", name="A", created_at=now, updated_at=now),
            Portfolio(id="portfolio-b", user_id="user-b", name="B", created_at=now, updated_at=now),
        ])
        session.add(PortfolioPosition(
            id="position-a", portfolio_id="portfolio-a", symbol="AAA.NS", name="A", quantity=1,
            average_buy_price=100, created_at=now, updated_at=now,
        ))
        session.commit()
        repository = PortfolioRepository(session)
        assert repository.list_positions("portfolio-a", "user-b") == []
        assert len(repository.list_positions("portfolio-a", "user-a")) == 1
