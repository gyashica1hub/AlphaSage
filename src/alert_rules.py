"""Pure alert-rule evaluation, kept independent from providers and delivery."""


def is_triggered(rule: str, threshold: float, quote: dict) -> bool:
    price = quote.get("price")
    change_pct = quote.get("change_pct")
    if rule == "price_above":
        return price is not None and price >= threshold
    if rule == "price_below":
        return price is not None and price <= threshold
    if rule == "change_pct_above":
        return change_pct is not None and change_pct >= threshold
    if rule == "change_pct_below":
        return change_pct is not None and change_pct <= threshold
    return False
