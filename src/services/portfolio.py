"""Business services for tenant-scoped portfolio operations."""

from src.repositories.portfolio import PortfolioRepository


class PortfolioService:
    def __init__(self, repository: PortfolioRepository):
        self.repository = repository

    def positions_for_user(self, portfolio_id: str, user_id: str):
        return self.repository.list_positions(portfolio_id, user_id)
