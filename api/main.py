"""FastAPI entry point for the AlphaSage web frontend."""

import csv
import hashlib
import json
import os
import secrets
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

import requests
import pandas as pd
from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import yfinance as yf
from dotenv import load_dotenv

from src.fetch_prices import get_historical_data, get_portfolio_with_live_prices
from src.logging_config import configure_logging
from src.db.models import Alert, AlertDelivery, ForecastRecord, Note, PortfolioPosition, ResearchDocument, Transaction, User, Watchlist, WatchlistItem
from src.db.sqlite import initialize_database
from src.db.session import get_session
from src.auth import create_email_verification_otp, create_password_reset_otp, create_session_token, create_user, find_user_by_email, hash_password, read_session_token, verify_email_verification_otp, verify_password, verify_password_reset_otp
from src.email_service import send_email_verification_otp, send_password_reset_otp
import logging
from src.portfolio_analytics import diversification_score, performers, risk_score
from src.risk_metrics import historical_risk_metrics
from src.technical_indicators import exponential_moving_average, relative_strength_index, simple_moving_average
from src.forecast_baseline import baseline_forecast
from src.analytics_baseline import walk_forward_sma_backtest
from src.research_retrieval import rank_documents
from src.portfolio_manager import add_stock, load_portfolio_raw, remove_stock
from src.market_data import MarketDataService
from src.market_cache import MarketCache
from src.alert_service import evaluate_alerts

load_dotenv()
configure_logging()
initialize_database()
market_data = MarketDataService(cache=MarketCache())

app = FastAPI(title="AlphaSage API", version="0.1.0")
NSE_UNIVERSE_FILE = Path(__file__).resolve().parents[1] / "data" / "nse_equity.csv"
NIFTY100_UNIVERSE_FILE = Path(__file__).resolve().parents[1] / "data" / "nifty100_universe.csv"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|172\.\d+\.\d+\.\d+)(:\d+)?$",
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


class TransactionCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    side: str = Field(pattern="^(BUY|SELL)$")
    quantity: float = Field(gt=0)
    price: float = Field(ge=0)
    executed_at: datetime | None = None


class WatchlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class WatchlistItemCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)


class NoteCreate(BaseModel):
    symbol: str | None = Field(default=None, max_length=30)
    body: str = Field(min_length=1, max_length=5000)


class AlertCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    rule: str = Field(pattern="^(price_above|price_below|change_pct_above|change_pct_below)$")
    threshold: float
    cooldown_minutes: int = Field(default=60, ge=1, le=10080)


class ForecastRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    model_name: str = Field(default="baseline_sma", pattern="^baseline_sma$")


class ResearchDocumentCreate(BaseModel):
    symbol: str | None = Field(default=None, max_length=30)
    source_url: str = Field(min_length=1, max_length=1000)
    source_title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=20, max_length=200000)


class NewsArticle(BaseModel):
    title: str
    url: str
    source: str
    published_at: str | None = None
    description: str | None = None


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    display_name: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)


class PasswordResetConfirm(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    otp: str = Field(pattern=r"^\d{6}$")
    password: str = Field(min_length=8, max_length=200)


class EmailVerificationRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    otp: str = Field(pattern=r"^\d{6}$")


GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def _google_configured() -> bool:
    return bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))


@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterRequest, response: Response) -> dict:
    if find_user_by_email(payload.email):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = create_user(payload.email, payload.password, payload.display_name)
    otp = create_email_verification_otp(user.id)
    try:
        send_email_verification_otp(user.email, otp)
    except Exception:
        logging.getLogger(__name__).exception("email_verification_send_failed")
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "email_verified": False}


@app.post("/api/auth/login")
def login(payload: LoginRequest, response: Response) -> dict:
    user = find_user_by_email(payload.email)
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before signing in")
    response.set_cookie("alphasage_session", create_session_token(user.id), httponly=True, samesite="lax", secure=False, max_age=604800)
    return {"id": user.id, "email": user.email, "display_name": user.display_name}


@app.get("/api/auth/google/start")
def google_start(response: Response) -> RedirectResponse:
    if not _google_configured():
        raise HTTPException(status_code=503, detail="Google sign-in is not configured")
    state = secrets.token_urlsafe(32)
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    query = urlencode({
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    })
    redirect = RedirectResponse(f"{GOOGLE_AUTHORIZATION_URL}?{query}")
    redirect.set_cookie("alphasage_google_state", state, httponly=True, samesite="lax", secure=False, max_age=600)
    return redirect


@app.get("/api/auth/google/callback")
def google_callback(code: str | None = None, state: str | None = None, error: str | None = None, alphasage_google_state: str | None = Cookie(default=None)) -> RedirectResponse:
    frontend_url = os.getenv("APP_BASE_URL", "http://localhost:3001")
    if error or not code or not state or not secrets.compare_digest(state, alphasage_google_state or ""):
        return RedirectResponse(f"{frontend_url}/?auth_error=google_sign_in_failed")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    try:
        token_response = requests.post(
            GOOGLE_TOKEN_URL,
            data={"code": code, "client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"], "redirect_uri": redirect_uri, "grant_type": "authorization_code"},
            timeout=10,
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise ValueError("Google did not return an access token")
        profile_response = requests.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
        profile_response.raise_for_status()
        profile = profile_response.json()
        email = str(profile.get("email", "")).lower().strip()
        if not email or not profile.get("email_verified"):
            raise ValueError("Google email is not verified")
    except (requests.RequestException, ValueError, KeyError):
        logging.getLogger(__name__).exception("google_sign_in_failed")
        return RedirectResponse(f"{frontend_url}/?auth_error=google_sign_in_failed")
    user = find_user_by_email(email)
    if not user:
        user = create_user(email, secrets.token_urlsafe(32), profile.get("name"))
    with get_session() as session:
        stored_user = session.get(User, user.id)
        stored_user.email_verified = True
        stored_user.display_name = stored_user.display_name or profile.get("name")
        session.commit()
    redirect = RedirectResponse(frontend_url)
    redirect.set_cookie("alphasage_session", create_session_token(user.id), httponly=True, samesite="lax", secure=False, max_age=604800)
    redirect.delete_cookie("alphasage_google_state")
    return redirect


@app.post("/api/auth/logout")
def logout(response: Response) -> dict:
    response.delete_cookie("alphasage_session")
    return {"status": "signed_out"}


@app.get("/api/auth/me")
def current_user(alphasage_session: str | None = Cookie(default=None)) -> dict:
    user_id = read_session_token(alphasage_session or "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Session user not found")
        return {"id": user.id, "email": user.email, "display_name": user.display_name}


@app.post("/api/auth/verify-email")
def verify_email(payload: EmailVerificationRequest, response: Response) -> dict:
    user_id = verify_email_verification_otp(payload.email, payload.otp)
    if not user_id:
        raise HTTPException(status_code=400, detail="Verification code is invalid or expired")
    with get_session() as session:
        user = session.get(User, user_id)
        response.set_cookie("alphasage_session", create_session_token(user.id), httponly=True, samesite="lax", secure=False, max_age=604800)
        return {"id": user.id, "email": user.email, "display_name": user.display_name, "email_verified": True}


@app.post("/api/auth/forgot-password")
def forgot_password(payload: PasswordResetRequest) -> dict:
    user = find_user_by_email(payload.email)
    # Do not reveal whether an email exists.
    if user:
        otp = create_password_reset_otp(user.id)
        try:
            send_password_reset_otp(user.email, otp)
        except Exception:
            logging.getLogger(__name__).exception("password_reset_email_failed")
    return {"message": "If an account exists, a reset code has been sent to your email."}


@app.post("/api/auth/reset-password")
def reset_password(payload: PasswordResetConfirm) -> dict:
    user_id = verify_password_reset_otp(payload.email, payload.otp)
    if not user_id:
        raise HTTPException(status_code=400, detail="Reset link is invalid or expired")
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=400, detail="Reset link is invalid or expired")
        user.password_hash = hash_password(payload.password)
        user.updated_at = datetime.now(UTC)
        session.commit()
    return {"message": "Password updated successfully"}


def _portfolio_response(user_id: str = "demo-user") -> dict:
    raw = load_portfolio_raw(user_id)
    enriched = get_portfolio_with_live_prices(raw["holdings"])
    best, worst = performers(enriched)
    invested = sum(item["invested_value"] for item in enriched)
    current_values = [item["current_value"] for item in enriched if item["current_value"] is not None]
    current = sum(current_values) if current_values else None
    pnl = current - invested if current is not None else None
    unavailable_count = sum(item["price_status"] == "unavailable" for item in enriched)
    available_count = len(enriched) - unavailable_count
    data_status = "unavailable" if not available_count and enriched else "partial" if unavailable_count else "available"
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
        "data_quality": {
            "status": data_status,
            "available_count": available_count,
            "unavailable_count": unavailable_count,
            "checked_at": datetime.now(UTC).isoformat(),
        },
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "alphasage-api"}


def require_user(alphasage_session: str | None = Cookie(default=None)) -> User:
    user_id = read_session_token(alphasage_session or "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Session user not found")
        return user


@app.get("/api/portfolio")
def get_portfolio(user: User = Depends(require_user)) -> dict:
    return _portfolio_response(user.id)


@app.get("/api/portfolio/risk")
def get_portfolio_risk(user: User = Depends(require_user)) -> dict:
    """Return historical risk metrics for the authenticated user's holdings."""
    raw = load_portfolio_raw(user.id)
    metrics = []
    for holding in raw["holdings"]:
        history = get_historical_data(holding["symbol"], period="6mo")
        prices = history["Close"].tolist() if not history.empty and "Close" in history else []
        metrics.append({"symbol": holding["symbol"], **historical_risk_metrics(prices)})
    available = [item for item in metrics if item["status"] == "ok"]
    return {
        "portfolio_id": raw["portfolio_id"],
        "metrics": metrics,
        "data_quality": {
            "available_count": len(available),
            "unavailable_count": len(metrics) - len(available),
            "checked_at": datetime.now(UTC).isoformat(),
        },
    }


@app.get("/api/analytics/models")
def list_analytics_models() -> list[dict]:
    return [{"name": "baseline_sma", "version": "1.0", "type": "baseline", "status": "active", "description": "Trailing moving-average forecast with empirical interval."}]


@app.post("/api/analytics/forecast", status_code=201)
def create_forecast(request: ForecastRequest, user: User = Depends(require_user)) -> dict:
    symbol = request.symbol.strip().upper()
    history = get_historical_data(symbol, period="max")
    prices = history["Close"].tolist() if not history.empty and "Close" in history else []
    forecast = baseline_forecast(prices, window=20)
    validation = walk_forward_sma_backtest(pd.Series(prices), window=20)
    if forecast.get("status") != "ok":
        raise HTTPException(status_code=422, detail="Not enough historical data for a forecast")
    indicators = {"sma_20": simple_moving_average(pd.Series(prices), 20).iloc[-1], "ema_20": exponential_moving_average(pd.Series(prices), 20).iloc[-1], "rsi_14": relative_strength_index(pd.Series(prices), 14).iloc[-1]}
    now = datetime.now(UTC)
    record = ForecastRecord(id=str(uuid.uuid4()), user_id=user.id, symbol=symbol, model_name=request.model_name, model_version="1.0", forecast=float(forecast["forecast"]), lower_bound=float(forecast["lower_bound"]), upper_bound=float(forecast["upper_bound"]), feature_snapshot=json.dumps({key: float(value) for key, value in indicators.items() if pd.notna(value)}), validation_snapshot=json.dumps(validation), created_at=now)
    with get_session() as session:
        session.add(record)
        session.commit()
    return {"id": record.id, "symbol": symbol, "model_name": record.model_name, "model_version": record.model_version, "forecast": forecast, "validation": validation, "created_at": now.isoformat()}


@app.get("/api/analytics/forecast-history")
def get_forecast_history(symbol: str | None = None, user: User = Depends(require_user)) -> list[dict]:
    with get_session() as session:
        query = session.query(ForecastRecord).filter(ForecastRecord.user_id == user.id)
        if symbol:
            query = query.filter(ForecastRecord.symbol == symbol.strip().upper())
        rows = query.order_by(ForecastRecord.created_at.desc()).limit(100).all()
    return [{"id": row.id, "symbol": row.symbol, "model_name": row.model_name, "model_version": row.model_version, "forecast": row.forecast, "lower_bound": row.lower_bound, "upper_bound": row.upper_bound, "features": json.loads(row.feature_snapshot), "validation": json.loads(row.validation_snapshot), "created_at": row.created_at.isoformat()} for row in rows]


@app.post("/api/research/documents", status_code=201)
def ingest_research_document(document: ResearchDocumentCreate, user: User = Depends(require_user)) -> dict:
    content = document.content.strip()
    record = ResearchDocument(id=str(uuid.uuid4()), user_id=user.id, symbol=document.symbol.strip().upper() if document.symbol else None, source_url=document.source_url.strip(), source_title=document.source_title.strip(), content=content, content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(), created_at=datetime.now(UTC))
    with get_session() as session:
        session.add(record)
        session.commit()
    return {"id": record.id, "symbol": record.symbol, "source_url": record.source_url, "source_title": record.source_title, "content_hash": record.content_hash, "created_at": record.created_at.isoformat()}


@app.get("/api/research/documents")
def list_research_documents(user: User = Depends(require_user)) -> list[dict]:
    with get_session() as session:
        rows = session.query(ResearchDocument).filter(ResearchDocument.user_id == user.id).order_by(ResearchDocument.created_at.desc()).limit(100).all()
    return [{"id": row.id, "symbol": row.symbol, "source_url": row.source_url, "source_title": row.source_title, "content_hash": row.content_hash, "created_at": row.created_at.isoformat()} for row in rows]


@app.get("/api/research/search")
def search_research_documents(query: str, symbol: str | None = None, user: User = Depends(require_user)) -> dict:
    with get_session() as session:
        rows = session.query(ResearchDocument).filter(ResearchDocument.user_id == user.id).all()
    documents = [{"id": row.id, "symbol": row.symbol, "source_url": row.source_url, "source_title": row.source_title, "content": row.content, "created_at": row.created_at.isoformat()} for row in rows]
    results = rank_documents(documents, query, symbol=symbol)
    return {"query": query, "symbol": symbol.upper() if symbol else None, "results": results, "citation_required": True}


@app.get("/api/news")
def get_news(query: str = "Indian stock market", page_size: int = 12, user: User = Depends(require_user)) -> dict:
    """Return linked headlines from the configured provider; never fabricate news."""
    api_key = os.getenv("NEWS_API_KEY", "")
    if not api_key:
        return {"articles": [], "status": "News provider is not configured"}
    response = requests.get("https://newsapi.org/v2/everything", params={"q": query, "language": "en", "sortBy": "publishedAt", "pageSize": min(page_size, 50), "apiKey": api_key}, timeout=12)
    if not response.ok:
        return {"articles": [], "status": "News provider unavailable"}
    articles = []
    for article in response.json().get("articles", []):
        if article.get("title") and article.get("url"):
            articles.append({"title": article["title"], "url": article["url"], "source": (article.get("source") or {}).get("name") or "Unknown source", "published_at": article.get("publishedAt"), "description": article.get("description")})
    return {"articles": articles, "status": "Live provider headlines"}


@app.post("/api/portfolio/transactions", status_code=201)
def create_transaction(transaction: TransactionCreate, user: User = Depends(require_user)) -> dict:
    portfolio_id = load_portfolio_raw(user.id)["portfolio_id"]
    with get_session() as session:
        symbol = transaction.symbol.upper()
        position = session.query(PortfolioPosition).filter(PortfolioPosition.portfolio_id == portfolio_id, PortfolioPosition.symbol == symbol).first()
        if transaction.side == "BUY":
            if position:
                total_quantity = position.quantity + transaction.quantity
                position.average_buy_price = round(((position.quantity * position.average_buy_price) + (transaction.quantity * transaction.price)) / total_quantity, 2)
                position.quantity = total_quantity
                position.updated_at = datetime.now(UTC)
            else:
                now = datetime.now(UTC)
                session.add(PortfolioPosition(id=str(uuid.uuid4()), portfolio_id=portfolio_id, symbol=symbol, name=symbol.replace(".NS", "").replace(".BO", ""), quantity=transaction.quantity, average_buy_price=transaction.price, sector="Other", created_at=now, updated_at=now))
        elif not position or position.quantity < transaction.quantity:
            raise HTTPException(status_code=400, detail="Sell quantity exceeds the current holding")
        else:
            position.quantity = round(position.quantity - transaction.quantity, 8)
            position.updated_at = datetime.now(UTC)
            if position.quantity == 0:
                session.delete(position)
        session.add(Transaction(
            id=str(uuid.uuid4()), portfolio_id=portfolio_id,
            symbol=symbol, side=transaction.side,
            quantity=transaction.quantity, price=transaction.price,
            executed_at=transaction.executed_at or datetime.now(UTC),
        ))
        session.commit()
    return {"status": "created", "portfolio_id": portfolio_id}


@app.get("/api/portfolio/transactions")
def list_transactions(user: User = Depends(require_user)) -> list[dict]:
    portfolio_id = load_portfolio_raw(user.id)["portfolio_id"]
    with get_session() as session:
        rows = session.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).order_by(Transaction.executed_at.desc()).all()
        return [
            {"id": row.id, "symbol": row.symbol, "side": row.side, "quantity": row.quantity, "price": row.price, "executed_at": row.executed_at.isoformat()}
            for row in rows
        ]


@app.delete("/api/portfolio/transactions/{transaction_id}")
def delete_transaction(transaction_id: str, user: User = Depends(require_user)) -> dict:
    portfolio_id = load_portfolio_raw(user.id)["portfolio_id"]
    with get_session() as session:
        row = session.query(Transaction).filter(Transaction.id == transaction_id, Transaction.portfolio_id == portfolio_id).first()
        if row is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        session.delete(row)
        session.commit()
    return {"status": "deleted", "id": transaction_id}


@app.get("/api/watchlists")
def get_watchlists(user: User = Depends(require_user)) -> list[dict]:
    with get_session() as session:
        rows = session.query(Watchlist).filter(Watchlist.user_id == user.id).all()
        return [{"id": row.id, "name": row.name} for row in rows]


@app.post("/api/watchlists", status_code=201)
def create_watchlist(payload: WatchlistCreate, user: User = Depends(require_user)) -> dict:
    now = datetime.now(UTC)
    row = Watchlist(id=str(uuid.uuid4()), user_id=user.id, name=payload.name, created_at=now, updated_at=now)
    with get_session() as session:
        session.add(row)
        session.commit()
    return {"id": row.id, "name": row.name}


@app.get("/api/watchlists/{watchlist_id}/items")
def get_watchlist_items(watchlist_id: str, user: User = Depends(require_user)) -> list[dict]:
    with get_session() as session:
        owned = session.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.user_id == user.id).first()
        if owned is None:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        rows = session.query(WatchlistItem).filter(WatchlistItem.watchlist_id == watchlist_id).all()
        return [{"id": row.id, "symbol": row.symbol, "created_at": row.created_at.isoformat()} for row in rows]


@app.post("/api/watchlists/{watchlist_id}/items", status_code=201)
def add_watchlist_item(watchlist_id: str, payload: WatchlistItemCreate, user: User = Depends(require_user)) -> dict:
    with get_session() as session:
        owned = session.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.user_id == user.id).first()
        if owned is None:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        row = WatchlistItem(id=str(uuid.uuid4()), watchlist_id=watchlist_id, symbol=payload.symbol.upper(), created_at=datetime.now(UTC))
        session.add(row)
        try:
            session.commit()
        except Exception as error:
            session.rollback()
            raise HTTPException(status_code=409, detail="Symbol already exists in watchlist") from error
        return {"id": row.id, "symbol": row.symbol}


@app.delete("/api/watchlists/{watchlist_id}/items/{symbol}")
def remove_watchlist_item(watchlist_id: str, symbol: str, user: User = Depends(require_user)) -> dict:
    with get_session() as session:
        owned = session.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.user_id == user.id).first()
        if owned is None:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        row = session.query(WatchlistItem).filter(WatchlistItem.watchlist_id == watchlist_id, WatchlistItem.symbol == symbol.upper()).first()
        if row is None:
            raise HTTPException(status_code=404, detail="Watchlist symbol not found")
        session.delete(row)
        session.commit()
    return {"status": "deleted", "symbol": symbol.upper()}


@app.post("/api/notes", status_code=201)
def create_note(payload: NoteCreate, user: User = Depends(require_user)) -> dict:
    now = datetime.now(UTC)
    row = Note(id=str(uuid.uuid4()), user_id=user.id, symbol=payload.symbol, body=payload.body, created_at=now, updated_at=now)
    with get_session() as session:
        session.add(row)
        session.commit()
    return {"id": row.id, "symbol": row.symbol, "body": row.body}


@app.get("/api/notes")
def get_notes(user: User = Depends(require_user)) -> list[dict]:
    with get_session() as session:
        rows = session.query(Note).filter(Note.user_id == user.id).order_by(Note.created_at.desc()).all()
        return [{"id": row.id, "symbol": row.symbol, "body": row.body, "created_at": row.created_at.isoformat()} for row in rows]


@app.post("/api/alerts", status_code=201)
def create_alert(payload: AlertCreate, user: User = Depends(require_user)) -> dict:
    row = Alert(id=str(uuid.uuid4()), user_id=user.id, symbol=payload.symbol.upper(), rule=payload.rule, threshold=payload.threshold, active=True, cooldown_minutes=payload.cooldown_minutes, created_at=datetime.now(UTC))
    with get_session() as session:
        session.add(row)
        session.commit()
    return {"id": row.id, "symbol": row.symbol, "rule": row.rule, "threshold": row.threshold, "cooldown_minutes": row.cooldown_minutes, "active": row.active}


@app.get("/api/alerts")
def get_alerts(user: User = Depends(require_user)) -> list[dict]:
    with get_session() as session:
        rows = session.query(Alert).filter(Alert.user_id == user.id).order_by(Alert.created_at.desc()).all()
        return [{"id": row.id, "symbol": row.symbol, "rule": row.rule, "threshold": row.threshold, "cooldown_minutes": row.cooldown_minutes, "last_triggered_at": row.last_triggered_at.isoformat() if row.last_triggered_at else None, "active": row.active} for row in rows]


@app.post("/api/alerts/evaluate")
def evaluate_user_alerts(user: User = Depends(require_user)) -> dict:
    with get_session() as session:
        results = evaluate_alerts(session, market_data)
    return {"results": results}


@app.get("/api/alerts/deliveries")
def get_alert_deliveries(user: User = Depends(require_user)) -> list[dict]:
    with get_session() as session:
        rows = session.query(AlertDelivery).filter(AlertDelivery.user_id == user.id).order_by(AlertDelivery.created_at.desc()).limit(50).all()
        return [{"id": row.id, "alert_id": row.alert_id, "channel": row.channel, "status": row.status, "message": row.message, "error": row.error, "created_at": row.created_at.isoformat()} for row in rows]


@app.delete("/api/alerts/{alert_id}")
def delete_alert(alert_id: str, user: User = Depends(require_user)) -> dict:
    with get_session() as session:
        row = session.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user.id).first()
        if row is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        session.delete(row)
        session.commit()
    return {"status": "deleted", "id": alert_id}


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


def _indianapi_stock_data(symbol: str) -> dict | None:
    """Fetch an Indian equity quote without exposing the provider key to the browser."""
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
        price = data.get("ltp") or data.get("last_price") or data.get("close") or data.get("current_price")
        if price is None:
            return None
        previous = data.get("previous_close") or data.get("prev_close") or data.get("previousClose")
        change = data.get("change") or data.get("day_change")
        change_pct = data.get("change_percent") or data.get("day_change_percent") or data.get("pChange")
        if change_pct is None and change is not None and previous:
            change_pct = float(change) / float(previous) * 100
        return {
            "symbol": symbol.upper(),
            "name": data.get("company_name") or data.get("name") or symbol.upper(),
            "exchange": "NSE",
            "sector": data.get("sector") or "Other",
            "price": float(price),
            "change": float(change) if change is not None else None,
            "change_pct": float(change_pct) if change_pct is not None else None,
            "high": data.get("day_high") or data.get("high"),
            "low": data.get("day_low") or data.get("low"),
            "previous_close": previous,
            "volume": data.get("volume"),
            "status": "IndianAPI market data",
        }
    except (requests.RequestException, ValueError, TypeError):
        return None
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
    return market_data.quote(symbol)


@app.post("/api/stocks/refresh")
def refresh_stock(symbol: str) -> dict:
    return market_data.refresh(symbol)


@app.get("/api/market-data/status")
def market_data_status() -> dict:
    return market_data.status()


@app.get("/api/stocks/dashboard")
def stock_dashboard(symbol: str) -> dict:
    ticker = symbol.strip().upper()
    details = stock_details(ticker)
    benchmark_symbol = "^NSEI" if ticker.endswith(".NS") else "^GSPC"
    history_points: list[dict] = []
    intraday_points: list[dict] = []
    benchmark_points: list[dict] = []
    fundamentals = {"market_cap": None, "pe_ratio": None, "dividend_yield": None, "week52_high": None, "week52_low": None}
    try:
        history_points = market_data.history(ticker, period="max")
        intraday_points = market_data.history(ticker, period="1d", interval="5m")
        benchmark_points = market_data.history(benchmark_symbol, period="max")
        info = yf.Ticker(ticker).info
        fundamentals = {"market_cap": info.get("marketCap"), "pe_ratio": info.get("trailingPE"), "dividend_yield": info.get("dividendYield"), "week52_high": info.get("fiftyTwoWeekHigh"), "week52_low": info.get("fiftyTwoWeekLow")}
    except Exception:
        logging.getLogger(__name__).warning("stock_dashboard_data_unavailable", extra={"symbol": ticker})
    stock_return = None
    benchmark_return = None
    if len(history_points) > 1:
        stock_return = round((history_points[-1]["close"] / history_points[0]["close"] - 1) * 100, 2)
    if len(benchmark_points) > 1:
        benchmark_return = round((benchmark_points[-1]["close"] / benchmark_points[0]["close"] - 1) * 100, 2)
    closes = pd.Series([point["close"] for point in history_points], dtype="float64")
    indicators: dict[str, float | None] = {"sma_20": None, "ema_20": None, "rsi_14": None}
    if len(closes) >= 20:
        indicators["sma_20"] = round(float(simple_moving_average(closes, 20).iloc[-1]), 2)
        indicators["ema_20"] = round(float(exponential_moving_average(closes, 20).iloc[-1]), 2)
    if len(closes) >= 15:
        rsi = relative_strength_index(closes, 14).iloc[-1]
        indicators["rsi_14"] = round(float(rsi), 2) if pd.notna(rsi) else None
    forecast = baseline_forecast(closes.tolist(), window=20)
    forecast_validation = walk_forward_sma_backtest(closes, window=20)
    return {**details, "history": history_points, "intraday_history": intraday_points, "benchmark": benchmark_points, "benchmark_symbol": benchmark_symbol, "stock_return_pct": stock_return, "benchmark_return_pct": benchmark_return, "history_quality": market_data.history_quality(history_points), "indicators": indicators, "forecast": forecast, "forecast_validation": forecast_validation, "corporate_actions": market_data.actions(ticker), "fundamentals": fundamentals}


@app.get("/api/market-overview")
def market_overview() -> list[dict]:
    instruments = [("NIFTY 50", "^NSEI", "India"), ("SENSEX", "^BSESN", "India"), ("S&P 500", "^GSPC", "United States"), ("Dow Jones", "^DJI", "United States"), ("NASDAQ", "^IXIC", "United States")]
    results = []
    for name, symbol, region in instruments:
        try:
            history = yf.Ticker(symbol).history(period="5d")
            if history.empty:
                raise ValueError("No market data")
            latest = history.iloc[-1]
            price = float(latest["Close"])
            previous = float(history.iloc[-2]["Close"]) if len(history) > 1 else price
            change = price - previous
            results.append({"name": name, "symbol": symbol, "region": region, "price": round(price, 2), "change": round(change, 2), "change_pct": round(change / previous * 100, 2) if previous else 0, "status": "Delayed provider data"})
        except Exception:
            results.append({"name": name, "symbol": symbol, "region": region, "price": None, "change_pct": None, "status": "Data unavailable"})
    return results


@app.post("/api/portfolio/holdings", status_code=201)
def create_holding(holding: HoldingCreate, user: User = Depends(require_user)) -> dict:
    add_stock(
        holding.symbol, holding.name, holding.quantity, holding.avg_buy_price,
        holding.buy_date or "", holding.sector, user.id,
    )
    portfolio_id = load_portfolio_raw(user.id)["portfolio_id"]
    with get_session() as session:
        session.add(Transaction(
            id=str(uuid.uuid4()), portfolio_id=portfolio_id,
            symbol=holding.symbol.upper(), side="BUY",
            quantity=holding.quantity, price=holding.avg_buy_price,
            executed_at=datetime.fromisoformat(holding.buy_date) if holding.buy_date else datetime.now(UTC),
        ))
        session.commit()
    return _portfolio_response(user.id)


@app.post("/api/portfolio/import", status_code=201)
def import_holdings(payload: HoldingsImport, user: User = Depends(require_user)) -> dict:
    if not payload.holdings:
        raise HTTPException(status_code=400, detail="No holdings supplied")
    for holding in payload.holdings:
        add_stock(
            holding.symbol, holding.name, holding.quantity, holding.avg_buy_price,
            holding.buy_date or "", holding.sector, user.id,
        )
    portfolio_id = load_portfolio_raw(user.id)["portfolio_id"]
    with get_session() as session:
        for holding in payload.holdings:
            session.add(Transaction(
                id=str(uuid.uuid4()), portfolio_id=portfolio_id,
                symbol=holding.symbol.upper(), side="BUY",
                quantity=holding.quantity, price=holding.avg_buy_price,
                executed_at=datetime.fromisoformat(holding.buy_date) if holding.buy_date else datetime.now(UTC),
            ))
        session.commit()
    return _portfolio_response(user.id)


@app.delete("/api/portfolio/holdings/{symbol}")
def delete_holding(symbol: str, user: User = Depends(require_user)) -> dict:
    existing = {item["symbol"] for item in load_portfolio_raw(user.id)["holdings"]}
    normalized = symbol.upper()
    if normalized not in existing:
        raise HTTPException(status_code=404, detail="Holding not found")
    remove_stock(normalized, user.id)
    return _portfolio_response(user.id)
