"""Reusable, deterministic risk metrics for historical close prices."""

from __future__ import annotations

import math


def _returns(prices: list[float]) -> list[float]:
    return [current / previous - 1 for previous, current in zip(prices, prices[1:], strict=False) if previous]


def historical_risk_metrics(prices: list[float], trading_days: int = 252) -> dict[str, float | int | str]:
    """Calculate annualized volatility, maximum drawdown, and downside deviation."""
    clean = [float(price) for price in prices if price is not None and float(price) > 0]
    if len(clean) < 2:
        return {"status": "insufficient_data", "observations": len(clean)}
    if trading_days <= 0:
        raise ValueError("trading_days must be positive")

    returns = _returns(clean)
    mean_return = sum(returns) / len(returns)
    variance = sum((value - mean_return) ** 2 for value in returns) / len(returns)
    volatility = math.sqrt(variance) * math.sqrt(trading_days)
    downside = [min(value, 0.0) ** 2 for value in returns]
    downside_deviation = math.sqrt(sum(downside) / len(downside)) * math.sqrt(trading_days)

    peak = clean[0]
    max_drawdown = 0.0
    for price in clean:
        peak = max(peak, price)
        max_drawdown = min(max_drawdown, price / peak - 1)

    return {
        "status": "ok",
        "observations": len(clean),
        "volatility": volatility,
        "max_drawdown": abs(max_drawdown),
        "downside_deviation": downside_deviation,
    }
