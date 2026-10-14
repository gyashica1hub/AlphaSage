# AlphaSage

### AI-powered investment intelligence for research, portfolio tracking, and risk-aware decisions

AlphaSage combines market data, portfolio analytics, financial news, machine learning, explainability, and a future evidence-backed multi-agent research workflow.

> AlphaSage is an educational and research tool, not a broker or financial adviser. Market data may be delayed or incomplete.

## Current capabilities

- Streamlit dashboard with light and dark themes
- Portfolio add/remove workflow with demo holdings
- yfinance historical/latest-price retrieval
- Plotly allocation, portfolio, and candlestick charts
- TextBlob sentiment with optional NewsAPI integration
- LSTM prediction with moving-average fallback
- Saved models and scalers
- RMSE/MAE evaluation and basic backtesting
- Approximate SHAP analysis through a Random Forest surrogate
- Optional Zerodha Kite Connect integration
- SQLite foundation for users, portfolios, positions, and watchlists
- JSON-to-SQLite demo importer
- Docker configuration and GitHub Actions CI
- Safe handling of unavailable market data

## Project status

This is an early-stage prototype. Planned production features include authentication, Google Sign-In, per-user authorization, transaction accounting, persistent watchlists, reliable background ingestion, mobile notifications, FinBERT, RAG, LangGraph agents, FastAPI, a production frontend, observability, and cloud deployment.

## Target architecture

    Next.js frontend / Streamlit internal UI
                    |
                    v
    FastAPI application layer
                    |
          Domain services and repositories
                    |
     PostgreSQL + Redis/SQS + S3
                    |
           Market data, RAG, ML, and agents

| Area | Current | Production direction |
|---|---|---|
| Interface | Streamlit | Next.js + TypeScript |
| API | Python modules | FastAPI |
| Database | SQLite | PostgreSQL; DynamoDB where appropriate |
| Market data | yfinance | Provider abstraction with licensed sources |
| Vector search | Planned ChromaDB | pgvector or managed vector database |
| Background work | Local scripts | SQS/Celery/Dramatiq workers |
| Storage | Local files | Amazon S3 |
| Authentication | Planned | Cognito/Auth0/managed OIDC |
| AI workflows | Planned | LangGraph with checkpoints |

## Repository structure

    AlphaSage/
    ├── app.py
    ├── requirements.txt
    ├── Dockerfile
    ├── docker-compose.yml
    ├── data/mock_portfolio.json
    ├── src/
    │   ├── config.py
    │   ├── fetch_prices.py
    │   ├── sentiment.py
    │   ├── predict.py
    │   ├── backtest.py
    │   ├── explainability.py
    │   ├── alerts.py
    │   ├── kite_integration.py
    │   └── db/
    │       ├── schema.sql
    │       ├── sqlite.py
    │       └── import_demo.py
    ├── tests/
    ├── .github/workflows/
    └── README.md

## Local setup

Python 3.11 or 3.12 is recommended.

### Windows PowerShell

    cd AlphaSage
    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    Copy-Item .env.example .env
    python -m streamlit run app.py

Open http://localhost:8501. If streamlit is not recognized, use python -m streamlit run app.py.

### macOS/Linux

    python3.11 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    cp .env.example .env
    python -m streamlit run app.py

## Configuration

Copy .env.example to .env:

    DATABASE_URL=sqlite:///data/stocksense.db
    ENVIRONMENT=development
    NEWS_API_KEY=
    KITE_API_KEY=
    KITE_API_SECRET=
    KITE_ACCESS_TOKEN=

Never commit .env, access tokens, API secrets, model artifacts, or private portfolio data.

## Local database

    python -m src.db.import_demo

This creates data/stocksense.db, which is ignored by Git. The JSON file is seed data only.

## Docker and quality checks

    docker compose up --build
    python -m compileall -q app.py src tests
    python -m pytest -q
    ruff check .

CI currently performs syntax checks and a Docker build. It will be expanded with tests, type checking, security scanning, and integration tests.

## Roadmap

### Phase 1 — Foundation

SQLite persistence, repositories, service boundaries, validation, migration, tests, and configuration checks.

### Phase 2 — Identity

Email/password authentication, secure hashing, Google OIDC, sessions, authorization, user portfolios, watchlists, notes, and saved analyses.

### Phase 3 — Portfolio product

Transaction ledger, realized/unrealized P&L, dividends, splits, fees, cash movements, CSV import/export, multi-currency, benchmarks, diversification, and concentration scores.

### Phase 4 — Market intelligence

Provider adapters, caching, retries, rate limits, corporate actions, freshness indicators, market overview, search, screeners, and earnings calendar.

### Phase 5 — Alerts

Price, percentage, technical, news, earnings, and risk alerts with background workers, cooldowns, deduplication, push, email, SMS, and delivery history.

### Phase 6 — RAG research assistant

Ingest annual reports, filings, investor presentations, earnings transcripts, company announcements, licensed news, and user notes. Use metadata filtering, keyword search, vector similarity, and reranking. Every answer must include citations, dates, source metadata, and uncertainty.

### Phase 7 — Multi-agent analysis

    Supervisor
     ├── Research agent
     ├── Fundamental-analysis agent
     ├── Technical-analysis agent
     ├── News and sentiment agent
     ├── Risk agent
     ├── Portfolio agent
     └── Evidence critic
               |
               v
        Cited final report

Agents will return structured claims, metrics, evidence, confidence, and limitations. The system will explain uncertainty instead of producing unsupported buy/sell claims.

## Security principles

- use managed authentication or reviewed OIDC;
- hash passwords with Argon2id or bcrypt;
- isolate every user-owned record by user_id;
- validate symbols, dates, quantities, and provider responses;
- store secrets in environment variables or a cloud secrets manager;
- never expose broker tokens to the browser;
- rate-limit authentication, search, and AI endpoints;
- log security events without secrets;
- show source timestamps and data freshness;
- require confirmation before any future trade action.

## GitHub

Repository: https://github.com/gyashica1hub/AlphaSage

    git checkout -b feature/short-description
    git add .
    git commit -m "Describe the change"
    git push -u origin feature/short-description

Do not commit .env, credentials, database files, or personal portfolio exports.

## Disclaimer

AlphaSage is for education, research, and portfolio organization. It does not provide guaranteed predictions, investment advice, or execution recommendations. Users are responsible for validating information and making their own decisions.

