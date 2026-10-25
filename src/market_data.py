"""Provider abstraction and short-lived cache for market quotes."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

import requests
import yfinance as yf

from src.market_cache import MarketCache

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderQuote:
    symbol: str
    name: str
    exchange: str
    sector: str
    price: float | None
    change: float | None
    change_pct: float | None
    high: float | None
    low: float | None
    previous_close: float | None
    volume: int | None
    provider: str


class QuoteProvider(Protocol):
    name: str

    def fetch(self, symbol: str) -> ProviderQuote | None:
        """Return a quote or None when this provider cannot serve the symbol."""


def _number(value: object) -> float | None:
    try:
        return float(str(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


class IndianApiProvider:
    name = "Indian API"

    def fetch(self, symbol: str) -> ProviderQuote | None:
        token = os.getenv("INDIAN_API_KEY")
        if not token:
            return None
        clean_symbol = symbol.upper().replace(".NS", "").replace(".BO", "")
        base_url = os.getenv("INDIAN_API_BASE_URL", "https://dev.indianapi.in").rstrip("/")
        response = requests.get(
            f"{base_url}/get_stock_data",
            params={"stock_name": clean_symbol},
            headers={"X-API-Key": token},
            timeout=6,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get(clean_symbol, payload) if isinstance(payload, dict) else {}
        if not isinstance(data, dict):
            return None
        price = data.get("ltp") or data.get("last_price") or data.get("close") or data.get("current_price")
        if price is None:
            return None
        previous = data.get("previous_close") or data.get("prev_close") or data.get("previousClose")
        change = data.get("change") or data.get("day_change")
        change_pct = data.get("change_percent") or data.get("day_change_percent") or data.get("pChange")
        if change_pct is None and change is not None and previous:
            change_pct = float(change) / float(previous) * 100
        return ProviderQuote(
            symbol=symbol.upper(), name=data.get("company_name") or data.get("name") or symbol.upper(),
            exchange="NSE", sector=data.get("sector") or "Other", price=_number(price), change=_number(change),
            change_pct=_number(change_pct), high=_number(data.get("day_high") or data.get("high")),
            low=_number(data.get("day_low") or data.get("low")), previous_close=_number(previous),
            volume=int(data["volume"]) if data.get("volume") is not None else None, provider=self.name,
        )


class FinnhubProvider:
    name = "Finnhub"

    def fetch(self, symbol: str) -> ProviderQuote | None:
        token = os.getenv("FINNHUB_API_KEY")
        if not token:
            return None
        base_symbol = symbol.replace(".NS", "").replace(".BO", "")
        quote = requests.get("https://finnhub.io/api/v1/quote", params={"symbol": base_symbol, "token": token}, timeout=5)
        profile = requests.get("https://finnhub.io/api/v1/stock/profile2", params={"symbol": base_symbol, "token": token}, timeout=5)
        quote.raise_for_status()
        profile.raise_for_status()
        data = quote.json()
        if not data.get("c"):
            return None
        identity = profile.json()
        return ProviderQuote(
            symbol=symbol.upper(), name=identity.get("name") or symbol.upper(), exchange=identity.get("exchange") or "Global",
            sector=identity.get("finnhubIndustry") or "Other", price=_number(data.get("c")), change=_number(data.get("d")),
            change_pct=_number(data.get("dp")), high=_number(data.get("h")), low=_number(data.get("l")),
            previous_close=_number(data.get("pc")), volume=None, provider=self.name,
        )


class YahooFinanceProvider:
    name = "Yahoo Finance"

    def fetch(self, symbol: str) -> ProviderQuote | None:
        history = yf.Ticker(symbol).history(period="5d")
        if history.empty:
            return None
        latest = history.iloc[-1]
        price = _number(latest.get("Close"))
        if price is None:
            return None
        previous = _number(history.iloc[-2].get("Close")) if len(history) > 1 else price
        change = price - previous if previous is not None else None
        return ProviderQuote(
            symbol=symbol.upper(), name=symbol.upper(), exchange=self.name, sector="Other", price=round(price, 2),
            change=round(change, 2) if change is not None else None,
            change_pct=round(change / previous * 100, 2) if change is not None and previous else 0,
            high=_number(latest.get("High")), low=_number(latest.get("Low")), previous_close=previous,
            volume=int(latest["Volume"]) if _number(latest.get("Volume")) is not None else None, provider=self.name,
        )


class MarketDataService:
    def __init__(self, providers: list[QuoteProvider] | None = None, ttl_seconds: int = 30, retry_attempts: int = 2, cache: MarketCache | None = None) -> None:
        self.providers = providers or [IndianApiProvider(), FinnhubProvider(), YahooFinanceProvider()]
        self.ttl_seconds = ttl_seconds
        self.retry_attempts = retry_attempts
        self.persistent_cache = cache
        self._cache: dict[str, tuple[float, dict]] = {}
        self.metrics = {"provider_calls": 0, "provider_failures": 0, "cache_hits": 0, "persistent_cache_hits": 0}

    def quote(self, symbol: str) -> dict:
        ticker = symbol.strip().upper()
        now = time.monotonic()
        cached = self._cache.get(ticker)
        if cached and now - cached[0] < self.ttl_seconds:
            result = {**cached[1], "cache": "hit"}
            self.metrics["cache_hits"] += 1
            return result
        if self.persistent_cache:
            cached_payload = self.persistent_cache.get_quote(ticker, self.ttl_seconds)
            if cached_payload:
                self._cache[ticker] = (now, cached_payload)
                self.metrics["persistent_cache_hits"] += 1
                return cached_payload

        for provider in self.providers:
            for attempt in range(self.retry_attempts):
                try:
                    self.metrics["provider_calls"] += 1
                    quote = provider.fetch(ticker)
                    if quote is None:
                        break
                    if quote.price is None or quote.price <= 0 or (quote.high is not None and quote.low is not None and quote.high < quote.low):
                        raise ValueError("provider returned invalid quote values")
                    result = {
                        "symbol": quote.symbol, "name": quote.name, "exchange": quote.exchange, "sector": quote.sector,
                        "price": quote.price, "change": quote.change, "change_pct": quote.change_pct, "high": quote.high,
                        "low": quote.low, "previous_close": quote.previous_close, "volume": quote.volume,
                        "status": "Live provider data" if provider.name != "Yahoo Finance" else "Delayed provider data",
                        "provider": quote.provider, "data_status": "fresh", "fetched_at": datetime.now(UTC).isoformat(),
                        "cache": "miss",
                    }
                    self._cache[ticker] = (now, result)
                    if self.persistent_cache:
                        self.persistent_cache.put_quote(ticker, result)
                    return result
                except Exception as error:  # providers are external and may raise library-specific errors
                    self.metrics["provider_failures"] += 1
                    logger.warning("market_provider_attempt_failed", extra={"provider": provider.name, "symbol": ticker, "attempt": attempt + 1, "error": str(error)})
                    if attempt + 1 < self.retry_attempts:
                        time.sleep(0.15 * (attempt + 1))

        result = {
            "symbol": ticker, "name": ticker, "exchange": "Unknown", "sector": "Other", "price": None,
            "status": "Price unavailable", "data_status": "unavailable", "provider": None,
            "fetched_at": datetime.now(UTC).isoformat(), "cache": "miss",
        }
        self._cache[ticker] = (now, result)
        if self.persistent_cache:
            self.persistent_cache.put_quote(ticker, result)
        return result

    def history(self, symbol: str, period: str = "6mo", interval: str = "1d") -> list[dict]:
        """Load historical OHLC data from the persistent cache or Yahoo Finance."""
        ticker = symbol.strip().upper()
        if self.persistent_cache:
            cached = self.persistent_cache.get_history(ticker, 900)
            if cached:
                return cached
        for attempt in range(self.retry_attempts):
            try:
                frame = yf.Ticker(ticker).history(period=period, interval=interval)
                points = []
                for index, row in frame.iterrows():
                    close = _number(row.get("Close"))
                    high = _number(row.get("High"))
                    low = _number(row.get("Low"))
                    if close is None or close <= 0 or (high is not None and low is not None and high < low):
                        logger.warning("market_history_invalid_point", extra={"symbol": ticker, "date": str(index)})
                        continue
                    points.append({"date": index.strftime("%Y-%m-%d"), "open": _number(row.get("Open")), "high": high, "low": low, "close": round(close, 2), "volume": int(row["Volume"]) if _number(row.get("Volume")) is not None else None})
                if self.persistent_cache:
                    self.persistent_cache.put_history(ticker, points)
                return points
            except Exception as error:
                logger.warning("market_history_attempt_failed", extra={"symbol": ticker, "attempt": attempt + 1, "error": str(error)})
                if attempt + 1 < self.retry_attempts:
                    time.sleep(0.15 * (attempt + 1))
        return []

    def actions(self, symbol: str) -> list[dict]:
        ticker = symbol.strip().upper()
        if self.persistent_cache:
            cached = self.persistent_cache.get_actions(ticker, 86400)
            if cached is not None:
                return cached
        try:
            frame = yf.Ticker(ticker).actions
            actions = []
            for index, row in frame.iterrows():
                for action in ("Dividends", "Stock Splits"):
                    value = _number(row.get(action))
                    if value:
                        actions.append({"date": index.strftime("%Y-%m-%d"), "type": action.lower().replace(" ", "_"), "value": value})
            if self.persistent_cache:
                self.persistent_cache.put_actions(ticker, actions)
            return actions
        except Exception as error:
            logger.warning("market_actions_unavailable", extra={"symbol": ticker, "error": str(error)})
            return []

    @staticmethod
    def history_quality(points: list[dict]) -> dict:
        dates = [point["date"] for point in points]
        invalid = sum(1 for point in points if point.get("close", 0) <= 0 or (point.get("high") is not None and point.get("low") is not None and point["high"] < point["low"]))
        return {"points": len(points), "invalid_points": invalid, "duplicate_dates": len(dates) - len(set(dates)), "status": "good" if points and invalid == 0 and len(dates) == len(set(dates)) else "incomplete"}

    def refresh(self, symbol: str) -> dict:
        ticker = symbol.strip().upper()
        self._cache.pop(ticker, None)
        if self.persistent_cache:
            self.persistent_cache.clear(ticker)
        quote = self.quote(ticker)
        return {**quote, "history": self.history(ticker)}

    def status(self) -> dict:
        return {**self.metrics, "providers": [provider.name for provider in self.providers], "quote_cache_ttl_seconds": self.ttl_seconds, "history_cache_ttl_seconds": 900}
