from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.models import Base, ResearchDocument, User


def test_research_documents_are_scoped_to_user() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.add_all([
            User(id="user-a", email="a@example.com", created_at=now, updated_at=now),
            User(id="user-b", email="b@example.com", created_at=now, updated_at=now),
            ResearchDocument(id="doc-a", user_id="user-a", symbol="INFY.NS", source_url="https://example.com", source_title="A", content="Revenue", content_hash="hash-a", created_at=now),
        ])
        session.commit()
        assert session.query(ResearchDocument).filter(ResearchDocument.user_id == "user-b").count() == 0
