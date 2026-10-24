from src.config import settings


def test_local_database_is_sqlite_by_default():
    assert settings.database_url.startswith("sqlite:///")


def test_secrets_are_not_hardcoded_in_config():
    assert settings.news_api_key == "" or not settings.news_api_key.startswith("sk-")
