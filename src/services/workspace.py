"""Application services for the user workspace domain."""

from src.repositories.workspace import WorkspaceRepository


class WorkspaceService:
    def __init__(self, repository: WorkspaceRepository):
        self.repository = repository

    def watchlists_for_user(self, user_id: str):
        return self.repository.watchlists_for_user(user_id)

    def transactions_for_user(self, portfolio_id: str, user_id: str):
        return self.repository.transactions_for_user(portfolio_id, user_id)

    def notes_for_user(self, user_id: str):
        return self.repository.notes_for_user(user_id)

    def alerts_for_user(self, user_id: str):
        return self.repository.alerts_for_user(user_id)
