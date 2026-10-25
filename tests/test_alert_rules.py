from src.alert_rules import is_triggered


def test_price_rules():
    quote = {"price": 101, "change_pct": 2}
    assert is_triggered("price_above", 100, quote)
    assert is_triggered("price_below", 101, quote)
    assert not is_triggered("price_below", 100, quote)


def test_change_rules_ignore_unavailable_data():
    assert is_triggered("change_pct_above", 5, {"change_pct": 5})
    assert is_triggered("change_pct_below", -5, {"change_pct": -6})
    assert not is_triggered("change_pct_above", 5, {"change_pct": None})
