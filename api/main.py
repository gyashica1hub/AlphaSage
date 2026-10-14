"""FastAPI entry point for the AlphaSage web frontend."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.fetch_prices import get_portfolio_with_live_prices
from src.portfolio_analytics import diversification_score, performers, risk_score
from src.portfolio_manager import add_stock, load_portfolio_raw, remove_stock

app = FastAPI(title="AlphaSage API", version="0.1.0")
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


@app.post("/api/portfolio/holdings", status_code=201)
def create_holding(holding: HoldingCreate) -> dict:
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
