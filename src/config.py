"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/stocksense.db")
    news_api_key: str = os.getenv("NEWS_API_KEY", "")
    environment: str = os.getenv("ENVIRONMENT", "development")


settings = Settings()
