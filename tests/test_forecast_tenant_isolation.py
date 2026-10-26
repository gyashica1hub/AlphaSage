from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.models import Base, ForecastRecord, User


def test_forecast_history_is_scoped_to_user() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.add_all([
            User(id="user-a", email="a@example.com", created_at=now, updated_at=now),
            User(id="user-b", email="b@example.com", created_at=now, updated_at=now),
            ForecastRecord(id="forecast-a", user_id="user-a", symbol="AAA.NS", model_name="baseline_sma", model_version="1.0", forecast=100, lower_bound=95, upper_bound=105, feature_snapshot="{}", validation_snapshot="{}", created_at=now),
        ])
        session.commit()
        assert session.query(ForecastRecord).filter(ForecastRecord.user_id == "user-b").count() == 0
        assert session.query(ForecastRecord).filter(ForecastRecord.user_id == "user-a").count() == 1
