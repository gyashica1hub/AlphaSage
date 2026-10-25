"""Refresh selected market symbols for a local scheduled job or worker."""

import logging
import sys

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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    symbols = sys.argv[1:]
    if not symbols:
        raise SystemExit("Usage: python -m src.market_refresh RELIANCE.NS TCS.NS")
    print(refresh_symbols(symbols))
