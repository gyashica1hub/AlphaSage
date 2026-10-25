from src.market_data import MarketDataService, ProviderQuote


class FakeProvider:
    name = "Test provider"

    def __init__(self, quote=None):
        self.quote = quote
        self.calls = 0

    def fetch(self, symbol):
        self.calls += 1
        return self.quote


def make_quote(symbol="TEST.NS"):
    return ProviderQuote(
        symbol=symbol,
        name="Test Company",
        exchange="NSE",
        sector="Technology",
        price=123.45,
        change=1.25,
        change_pct=1.02,
        high=125.0,
        low=120.0,
        previous_close=122.2,
        volume=1000,
        provider="Test provider",
    )


def test_market_data_cache_avoids_duplicate_provider_calls():
    provider = FakeProvider(make_quote())
    service = MarketDataService([provider], ttl_seconds=60)

    first = service.quote("test.ns")
    second = service.quote("TEST.NS")

    assert first["data_status"] == "fresh"
    assert first["cache"] == "miss"
    assert second["cache"] == "hit"
    assert provider.calls == 1


def test_market_data_reports_unavailable_without_fabricating_price():
    service = MarketDataService([FakeProvider()], ttl_seconds=60)

    result = service.quote("MISSING.NS")

    assert result["price"] is None
    assert result["data_status"] == "unavailable"
    assert result["status"] == "Price unavailable"
