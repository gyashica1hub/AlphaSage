"""
fetch_prices.py
----------------
Yeh module stock prices fetch karta hai yfinance (free, unlimited) se.
Jab real broker API (Kite Connect / Angel One SmartAPI) available ho,
bas is file ke functions ko replace karna hoga - baaki poora pipeline
(sentiment, prediction, dashboard) same rahega.

Function names jaanbujh kar Kite Connect jaisa rakhe hain, taaki
production mein migrate karna easy ho.
"""

import os
import logging
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _indianapi_price(symbol: str) -> float | None:
    token = os.getenv("INDIAN_API_KEY")
    if not token:
        return None
    clean_symbol = symbol.upper().replace(".NS", "").replace(".BO", "")
    base_url = os.getenv("INDIAN_API_BASE_URL", "https://dev.indianapi.in").rstrip("/")
    try:
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
        value = data.get("ltp") or data.get("last_price") or data.get("close") or data.get("current_price")
        return round(float(value), 2) if value is not None else None
    except (requests.RequestException, ValueError, TypeError):
        return None


def get_live_price(symbol: str) -> float:
    """
    Current/last traded price nikalta hai.
    Kite Connect mein iska equivalent: kite.ltp(symbol)
    """
    indian_price = _indianapi_price(symbol)
    if indian_price is not None:
        return indian_price
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if data.empty:
            return None
        return round(float(data["Close"].iloc[-1]), 2)
    except Exception as e:
        logger.warning("price_fetch_failed", extra={"symbol": symbol, "error": str(e)})
        return None


def get_historical_data(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """
    Historical OHLCV data nikalta hai - LSTM training/graphs ke liye use hota hai.
    Kite Connect mein iska equivalent: kite.historical_data(...)
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        logger.warning("history_fetch_failed", extra={"symbol": symbol, "error": str(e)})
        return pd.DataFrame()


def get_portfolio_with_live_prices(holdings: list) -> list:
    """
    Mock portfolio (buy price) ko live current price ke saath merge karta hai,
    P&L calculate karta hai - bilkul waise jaise Kite ka kite.holdings() karta hai.
    """
    enriched = []
    for stock in holdings:
        current_price = get_live_price(stock["symbol"])
        if current_price is None:
            enriched.append({
                **stock,
                "current_price": None,
                "invested_value": round(stock["quantity"] * stock["avg_buy_price"], 2),
                "current_value": None,
                "pnl": None,
                "pnl_pct": None,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "price_status": "unavailable",
            })
            continue

        invested = stock["quantity"] * stock["avg_buy_price"]
        current_value = stock["quantity"] * current_price
        pnl = round(current_value - invested, 2)
        pnl_pct = round((pnl / invested) * 100, 2) if invested else 0

        enriched.append({
            **stock,
            "current_price": current_price,
            "invested_value": round(invested, 2),
            "current_value": round(current_value, 2),
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "price_status": "fresh"
        })
    return enriched


if __name__ == "__main__":
    # quick test
    print(get_live_price("RELIANCE.NS"))
    print(get_historical_data("TCS.NS", period="1mo").tail())


def get_portfolio_value_history(holdings: list, period: str = "6mo") -> pd.DataFrame:
    """
    Poore portfolio ki total value ka time-series nikalta hai (Date, Value).
    Har stock ki historical closing price * quantity, sabko din ke hisaab se
    add kar deta hai - isse "Portfolio Performance" wala area chart banta hai.
    """
    frames = []
    for h in holdings:
        hist = get_historical_data(h["symbol"], period=period)
        if hist.empty:
            continue
        temp = hist[["Date", "Close"]].copy()
        temp["Value"] = temp["Close"] * h["quantity"]
        temp = temp[["Date", "Value"]].set_index("Date")
        temp.columns = [h["symbol"]]
        frames.append(temp)

    if not frames:
        return pd.DataFrame(columns=["Date", "Value"])

    combined = pd.concat(frames, axis=1)
    combined = combined.ffill().fillna(0)
    total = combined.sum(axis=1)
    result = total.reset_index()
    result.columns = ["Date", "Value"]
    return result
