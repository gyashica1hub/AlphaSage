"""Portfolio repository with explicit user ownership checks."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Portfolio, PortfolioPosition


class PortfolioRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_for_user(self, portfolio_id: str, user_id: str) -> Portfolio | None:
        return self.session.scalar(
            select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        )

    def list_positions(self, portfolio_id: str, user_id: str) -> list[PortfolioPosition]:
        portfolio = self.get_for_user(portfolio_id, user_id)
        if portfolio is None:
            return []
        return list(self.session.scalars(select(PortfolioPosition).where(PortfolioPosition.portfolio_id == portfolio.id)))
