"""Run persisted alert evaluation on a schedule."""

import logging
import sys
import time

from src.alert_service import evaluate_alerts
from src.db.session import get_session
from src.market_cache import MarketCache
from src.market_data import MarketDataService


def run(interval_seconds: int = 300) -> None:
    service = MarketDataService(cache=MarketCache())
    while True:
        with get_session() as session:
            evaluate_alerts(session, service)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 300)
