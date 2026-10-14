"""Deterministic portfolio insights for the AlphaSage dashboard."""

from collections import defaultdict
from math import sqrt


def _weights(portfolio: list[dict]) -> list[tuple[dict, float]]:
    valued = [p for p in portfolio if p.get("current_value") is not None]
    total = sum(p["current_value"] for p in valued)
    if not total:
        return []
    return [(p, p["current_value"] / total) for p in valued]


def diversification_score(portfolio: list[dict]) -> int | None:
    weighted = _weights(portfolio)
    if not weighted:
        return None
    concentration = sum(weight**2 for _, weight in weighted)
    sector_weights = defaultdict(float)
    for position, weight in weighted:
        sector_weights[position.get("sector") or "Other"] += weight
    sector_concentration = sum(weight**2 for weight in sector_weights.values())
    score = 100 * (1 - (0.7 * concentration + 0.3 * sector_concentration))
    return max(0, min(100, round(score)))


def risk_score(portfolio: list[dict]) -> int | None:
    weighted = _weights(portfolio)
    if not weighted:
        return None
    concentration = sum(weight**2 for _, weight in weighted)
    largest = max(weight for _, weight in weighted)
    score = 100 * (0.55 * concentration + 0.45 * largest)
    return max(0, min(100, round(score)))


def performers(portfolio: list[dict]) -> tuple[dict | None, dict | None]:
    available = [p for p in portfolio if p.get("pnl_pct") is not None]
    if not available:
        return None, None
    return max(available, key=lambda p: p["pnl_pct"]), min(available, key=lambda p: p["pnl_pct"])


def annual_dividend_estimate(portfolio: list[dict]) -> float | None:
    """Placeholder until dividend history is ingested by the market-data service."""
    if not any(p.get("current_value") is not None for p in portfolio):
        return None
    return 0.0
