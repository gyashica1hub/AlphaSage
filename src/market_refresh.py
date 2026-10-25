"""Refresh selected market symbols for a local scheduled job or worker."""

import logging
import sys
from threading import Event

from src.market_cache import MarketCache
from src.market_data import MarketDataService

logger = logging.getLogger(__name__)


def refresh_symbols(symbols: list[str]) -> list[dict]:
    service = MarketDataService(cache=MarketCache())
    results = []
    for symbol in dict.fromkeys(symbol.strip().upper() for symbol in symbols if symbol.strip()):
        result = service.refresh(symbol)
        results.append({"symbol": symbol, "status": result.get("data_status"), "price": result.get("price"), "history_points": len(result.get("history", []))})
    return results


def run_refresh_loop(symbols: list[str], interval_seconds: int = 300, stop_event: Event | None = None) -> None:
    """Run refresh cycles for a worker process until stop_event is set."""
    stop_event = stop_event or Event()
    while not stop_event.is_set():
        logger.info("market_refresh_cycle_started", extra={"symbols": symbols})
        refresh_symbols(symbols)
        stop_event.wait(interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    symbols = sys.argv[1:]
    if not symbols:
        raise SystemExit("Usage: python -m src.market_refresh RELIANCE.NS TCS.NS")
    print(refresh_symbols(symbols))
