"""FastAPI entry point for the AlphaSage web frontend."""

import csv
import os
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import yfinance as yf
from dotenv import load_dotenv

from src.fetch_prices import get_portfolio_with_live_prices
from src.portfolio_analytics import diversification_score, performers, risk_score
from src.portfolio_manager import add_stock, load_portfolio_raw, remove_stock

load_dotenv()

app = FastAPI(title="AlphaSage API", version="0.1.0")
NSE_UNIVERSE_FILE = Path(__file__).resolve().parents[1] / "data" / "nse_equity.csv"
NIFTY100_UNIVERSE_FILE = Path(__file__).resolve().parents[1] / "data" / "nifty100_universe.csv"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HoldingCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    name: str = Field(default="", max_length=120)
    quantity: float = Field(gt=0)
    avg_buy_price: float = Field(gt=0)
    buy_date: str | None = None
    sector: str = Field(default="Other", max_length=80)


class HoldingsImport(BaseModel):
    holdings: list[HoldingCreate]


def _portfolio_response() -> dict:
    raw = load_portfolio_raw()
    enriched = get_portfolio_with_live_prices(raw["holdings"])
    best, worst = performers(enriched)
    invested = sum(item["invested_value"] for item in enriched)
    current_values = [item["current_value"] for item in enriched if item["current_value"] is not None]
    current = sum(current_values) if current_values else None
    pnl = current - invested if current is not None else None
    return {
        "portfolio_id": raw["portfolio_id"],
        "holdings": enriched,
        "summary": {
            "total_value": current,
            "total_invested": invested,
            "total_pnl": pnl,
            "return_pct": (pnl / invested * 100) if pnl is not None and invested else None,
            "holdings_count": len(enriched),
            "best_performer": best,
            "worst_performer": worst,
            "diversification_score": diversification_score(enriched),
            "risk_score": risk_score(enriched),
        },
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "alphasage-api"}


@app.get("/api/portfolio")
def get_portfolio() -> dict:
    return _portfolio_response()


def _finnhub_search(query: str) -> list[dict]:
    token = os.getenv("FINNHUB_API_KEY")
    if not token:
        return []
    try:
        response = requests.get(
            "https://finnhub.io/api/v1/search",
            params={"q": query, "token": token},
            timeout=5,
        )
        response.raise_for_status()
        results = []
        for item in response.json().get("result", []):
            symbol = item.get("symbol")
            name = item.get("description")
            kind = item.get("type", "").upper()
            if symbol and name and kind in {"COMMON STOCK", "ETP", "ETF"}:
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "sector": "Other",
                    "exchange": item.get("displaySymbol", "Global"),
                })
        return results[:20]
    except (requests.RequestException, ValueError):
        return []


@app.get("/api/stocks/search")
def search_stocks(q: str) -> dict:
    query = q.strip()
    normalized = query.lower()
    if len(query) < 1:
        return {"results": []}
    local_results = []
    if normalized != "nse" and NIFTY100_UNIVERSE_FILE.exists():
        with NIFTY100_UNIVERSE_FILE.open(newline="", encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):
                symbol = (row.get("Symbol") or "").strip()
                name = (row.get("Company Name") or "").strip()
                industry = (row.get("Industry") or "Other").strip()
                show_all = normalized in {"nse", "nifty100", "nifty 100", "top100", "top 100"}
                if symbol and name and (show_all or normalized in symbol.lower() or normalized in name.lower()):
                    local_results.append({"symbol": f"{symbol}.NS", "name": name, "sector": industry, "exchange": "NIFTY 100"})
        if local_results:
            return {"results": local_results[:100]}
    if NSE_UNIVERSE_FILE.exists():
        with NSE_UNIVERSE_FILE.open(newline="", encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):
                symbol = (row.get("SYMBOL") or "").strip()
                name = (row.get("NAME OF COMPANY") or "").strip()
                if symbol and name and (normalized == "nse" or normalized in symbol.lower() or normalized in name.lower()):
                    local_results.append({"symbol": f"{symbol}.NS", "name": name, "sector": "Other", "exchange": "NSE"})
                    if normalized != "nse" and len(local_results) >= 25:
                        break
    if local_results:
        return {"results": local_results[:5000]}
    finnhub_results = _finnhub_search(query)
    if finnhub_results:
        return {"results": finnhub_results}
    try:
        quotes = yf.Search(query).quotes or []
        results = []
        for quote in quotes:
            if quote.get("quoteType") not in {"EQUITY", "ETF"}:
                continue
            symbol = quote.get("symbol")
            name = quote.get("longname") or quote.get("shortname") or symbol
            if symbol and name:
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "sector": "Other",
                    "exchange": quote.get("exchange", ""),
                })
        return {"results": results[:20]}
    except Exception:
        return {"results": []}


@app.get("/api/stocks/details")
def stock_details(symbol: str) -> dict:
    ticker = symbol.strip().upper()
    token = os.getenv("FINNHUB_API_KEY")
    if token:
        try:
            quote = requests.get("https://finnhub.io/api/v1/quote", params={"symbol": ticker.replace(".NS", ""), "token": token}, timeout=5).json()
            profile = requests.get("https://finnhub.io/api/v1/stock/profile2", params={"symbol": ticker.replace(".NS", ""), "token": token}, timeout=5).json()
            if quote.get("c"):
                return {"symbol": ticker, "name": profile.get("name") or ticker, "exchange": profile.get("exchange") or "Global", "sector": profile.get("finnhubIndustry") or "Other", "price": quote.get("c"), "change": quote.get("d"), "change_pct": quote.get("dp"), "high": quote.get("h"), "low": quote.get("l"), "previous_close": quote.get("pc"), "status": "Live provider data"}
        except (requests.RequestException, ValueError):
            pass
    try:
        history = yf.Ticker(ticker).history(period="5d")
        if not history.empty:
            latest = history.iloc[-1]
            price = float(latest["Close"])
            previous = float(history.iloc[-2]["Close"]) if len(history) > 1 else price
            change = price - previous
            return {"symbol": ticker, "name": ticker, "exchange": "Yahoo Finance", "sector": "Other", "price": round(price, 2), "change": round(change, 2), "change_pct": round(change / previous * 100, 2) if previous else 0, "high": float(latest["High"]), "low": float(latest["Low"]), "previous_close": round(previous, 2), "volume": int(latest["Volume"]), "status": "Delayed provider data"}
    except Exception:
        pass
    return {"symbol": ticker, "name": ticker, "exchange": "Unknown", "sector": "Other", "price": None, "status": "Price unavailable"}


@app.post("/api/portfolio/holdings", status_code=201)
def create_holding(holding: HoldingCreate) -> dict:
    add_stock(
        holding.symbol, holding.name, holding.quantity, holding.avg_buy_price,
        holding.buy_date or "", holding.sector,
    )
    return _portfolio_response()


@app.post("/api/portfolio/import", status_code=201)
def import_holdings(payload: HoldingsImport) -> dict:
    if not payload.holdings:
        raise HTTPException(status_code=400, detail="No holdings supplied")
    for holding in payload.holdings:
        add_stock(
            holding.symbol, holding.name, holding.quantity, holding.avg_buy_price,
            holding.buy_date or "", holding.sector,
        )
    return _portfolio_response()


@app.delete("/api/portfolio/holdings/{symbol}")
def delete_holding(symbol: str) -> dict:
    existing = {item["symbol"] for item in load_portfolio_raw()["holdings"]}
    normalized = symbol.upper()
    if normalized not in existing:
        raise HTTPException(status_code=404, detail="Holding not found")
    remove_stock(normalized)
    return _portfolio_response()
