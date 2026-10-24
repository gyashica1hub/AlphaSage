"""Tenant-safe repositories for workspace records."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Alert, Note, Transaction, Watchlist, WatchlistItem


class WorkspaceRepository:
    def __init__(self, session: Session):
        self.session = session

    def watchlists_for_user(self, user_id: str) -> list[Watchlist]:
        return list(self.session.scalars(select(Watchlist).where(Watchlist.user_id == user_id)))

    def watchlist_items_for_user(self, watchlist_id: str, user_id: str) -> list[WatchlistItem]:
        owned = self.session.scalar(select(Watchlist).where(Watchlist.id == watchlist_id, Watchlist.user_id == user_id))
        if owned is None:
            return []
        return list(self.session.scalars(select(WatchlistItem).where(WatchlistItem.watchlist_id == watchlist_id)))

    def transactions_for_user(self, portfolio_id: str, user_id: str) -> list[Transaction]:
        owned = self.session.scalar(select(Transaction).join(Transaction.portfolio).where(
            Transaction.portfolio_id == portfolio_id, Transaction.portfolio.has(user_id=user_id)
        ))
        if owned is None:
            return []
        return list(self.session.scalars(select(Transaction).where(Transaction.portfolio_id == portfolio_id)))

    def notes_for_user(self, user_id: str) -> list[Note]:
        return list(self.session.scalars(select(Note).where(Note.user_id == user_id)))

    def alerts_for_user(self, user_id: str) -> list[Alert]:
        return list(self.session.scalars(select(Alert).where(Alert.user_id == user_id)))
