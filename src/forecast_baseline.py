"""Transparent moving-average forecast used as a non-ML benchmark."""

from __future__ import annotations

import math


def baseline_forecast(prices: list[float], window: int = 20) -> dict[str, float | int | str]:
    """Forecast one next close and an empirical 95% interval.

    The interval is based on historical one-day changes and is descriptive,
    not a guarantee or investment recommendation.
    """
    clean = [float(price) for price in prices if price is not None and float(price) > 0]
    if window < 2:
        raise ValueError("window must be at least 2")
    if len(clean) < window + 1:
        return {"status": "insufficient_data", "observations": len(clean)}

    forecast = sum(clean[-window:]) / window
    returns = [current / previous - 1 for previous, current in zip(clean, clean[1:], strict=False) if previous]
    mean_return = sum(returns) / len(returns)
    variance = sum((value - mean_return) ** 2 for value in returns) / len(returns)
    interval = forecast * 1.96 * math.sqrt(variance)
    return {
        "status": "ok",
        "observations": len(clean),
        "method": f"{window}-day moving average",
        "forecast": forecast,
        "lower_bound": max(0.0, forecast - interval),
        "upper_bound": forecast + interval,
    }
