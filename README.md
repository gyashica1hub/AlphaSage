# AlphaSage

<p align="center">
  <strong>AI-Powered Investment Intelligence</strong><br>
  Research smarter. Understand risk. Make informed decisions.
</p>

<p align="center">
  <a href="https://github.com/gyashica1hub/AlphaSage/actions"><img src="https://github.com/gyashica1hub/AlphaSage/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Interface-Streamlit-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/License-Educational-lightgrey" alt="License">
</p>

## Overview

AlphaSage is a modern investment research and portfolio intelligence platform for investors who want a clearer understanding of market movements, portfolio performance, financial news, and model-driven insights.

The platform brings market data, portfolio analytics, sentiment analysis, machine learning forecasts, model evaluation, and explainability into a single professional workspace.

AlphaSage is designed with a modular architecture so that the initial research dashboard can evolve into a secure, multi-user investment intelligence product.

## Core capabilities

### Portfolio intelligence

- Portfolio value and invested-capital overview
- Current profit and loss calculations
- Position-level performance
- Portfolio allocation visualization
- Historical portfolio performance
- Add and remove holdings
- Development portfolio import
- SQLite-backed portfolio foundation

### Market analysis

- Historical OHLCV data
- Latest available market prices
- Interactive Plotly charts
- Candlestick visualization
- Multi-stock performance comparison
- Market-data availability indicators
- Optional Zerodha Kite Connect holdings integration

### Artificial intelligence and machine learning

- News headline sentiment analysis
- LSTM-based next-price forecasting
- Moving-average baseline fallback
- Saved model and scaler support
- RMSE and MAE evaluation
- Basic strategy-versus-buy-and-hold comparison
- Approximate feature attribution using a Random Forest surrogate and SHAP

### User experience

- Professional fintech-inspired interface
- Light and dark themes
- Responsive dashboard layout
- Interactive portfolio charts
- Clear unavailable-data handling
- Docker-based local execution

## Engineering approach

AlphaSage separates market-data access, portfolio calculations, sentiment analysis, prediction, explainability, alerts, and database utilities into independent modules.

The current application uses Streamlit as the user interface and SQLite for local persistence. The data and service boundaries are intentionally modular to support future API-based deployment, stronger authentication, background processing, and scalable storage without discarding the research logic already implemented.

## System design

    User interface
        |
        v
    Streamlit application
        |
        +-- Portfolio services
        +-- Market-data services
        +-- Sentiment analysis
        +-- Prediction and evaluation
        +-- Explainability
        +-- Alert evaluation
        |
        +-- SQLite development database
        +-- External market and news providers

The system is designed around provider adapters so market-data and news sources can be replaced without rewriting the dashboard and analytical modules.

## Technology stack

| Layer | Technology |
|---|---|
| Language | Python |
| User interface | Streamlit |
| Data analysis | Pandas, NumPy |
| Visualization | Plotly |
| Market data | yfinance |
| News sentiment | TextBlob, optional NewsAPI |
| Forecasting | TensorFlow/Keras LSTM |
| Explainability | SHAP with a Random Forest surrogate |
| Portfolio integration | Zerodha Kite Connect adapter |
| Local persistence | SQLite |
| Containerization | Docker, Docker Compose |
| Continuous integration | GitHub Actions |

## Repository structure

    AlphaSage/
    ├── app.py
    ├── requirements.txt
    ├── Dockerfile
    ├── docker-compose.yml
    ├── data/
    │   └── mock_portfolio.json
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
    └── .github/
        └── workflows/

## Getting started

### Requirements

- Python 3.11 or 3.12 recommended
- Git
- Internet access for external market and news providers
- Docker Desktop, optional

### Windows PowerShell

    cd AlphaSage
    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    Copy-Item .env.example .env
    python -m streamlit run app.py

Open http://localhost:8501.

If the streamlit command is unavailable, use:

    python -m streamlit run app.py

### macOS or Linux

    python3.11 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    cp .env.example .env
    python -m streamlit run app.py

## Configuration

Copy .env.example to .env and add only the integrations required for local development.

    DATABASE_URL=sqlite:///data/stocksense.db
    ENVIRONMENT=development

    NEWS_API_KEY=

    KITE_API_KEY=
    KITE_API_SECRET=
    KITE_ACCESS_TOKEN=

Never commit .env files, credentials, broker tokens, private portfolio exports, database files, or trained model artifacts.

## Local database

Initialize the local SQLite database and import the development portfolio:

    python -m src.db.import_demo

The local database is created at data/stocksense.db and is excluded from version control.

## Docker

    docker compose up --build

The dashboard will be available at http://localhost:8501.

## AlphaSage web frontend

The repository also contains a dedicated Next.js frontend in frontend/. It is the foundation for the production web experience, while the Streamlit application remains available for the current Python prototype and analytical validation.

    cd frontend
    npm install
    npm run dev

Open http://localhost:3000. The frontend uses the AlphaSage web API for portfolio data and remains available alongside the Streamlit analytical prototype.

Start the API in a second terminal:

    python -m uvicorn api.main:app --host 127.0.0.1 --port 8000

The API health endpoint is available at http://127.0.0.1:8000/health and the portfolio endpoint at http://127.0.0.1:8000/api/portfolio.

## Validation

    python -m compileall -q app.py src tests
    python -m pytest -q
    ruff check .

The continuous-integration workflow validates Python syntax and builds the Docker image. Additional automated tests and security checks should be added as the platform grows.

## Data integrity and reliability

AlphaSage treats unavailable market data as unavailable rather than substituting a stale purchase price. Analytical outputs should always be interpreted alongside their timestamp, source, coverage, and data quality.

Forecasts and sentiment scores are analytical signals, not guarantees. Model performance must be evaluated against time-ordered historical data and appropriate baselines before being used for decision support.

## Security and responsible use

- Credentials are supplied through environment variables and must not be committed.
- User-owned data must be isolated by authenticated user identity before public deployment.
- Broker integrations must use least-privilege access and secure token handling.
- External input must be validated before storage or analysis.
- Future execution functionality must require explicit user confirmation.
- AlphaSage does not provide guaranteed returns, investment advice, or trade execution.
- Users should verify market data and research with official sources.

## GitHub

Repository: https://github.com/gyashica1hub/AlphaSage

    git checkout -b feature/your-change
    git add .
    git commit -m "Describe the change"
    git push -u origin feature/your-change

## License and usage

This repository is intended for educational, research, and portfolio-analytics development. Add a formal open-source license before distributing the project publicly.

