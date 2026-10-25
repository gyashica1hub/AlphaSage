"""Leakage-safe baseline evaluation for daily close-price series."""

from __future__ import annotations

import numpy as np
import pandas as pd


def walk_forward_sma_backtest(
    prices: pd.Series,
    window: int = 5,
    test_fraction: float = 0.2,
) -> dict[str, float | int | str]:
    """Evaluate a moving-average forecast using only prices known at each step.

    The forecast for day ``t`` is calculated from ``t-window:t``. This makes
    the result a small, deterministic benchmark for future ML models.
    """
    if window < 2:
        raise ValueError("window must be at least 2")
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")

    clean = pd.to_numeric(prices, errors="coerce").dropna().astype(float)
    split = max(window, int(len(clean) * (1 - test_fraction)))
    if len(clean) <= split:
        return {"status": "insufficient_data", "test_points": 0}

    actual = clean.iloc[split:].to_numpy()
    predicted = np.array([clean.iloc[i - window:i].mean() for i in range(split, len(clean))])
    errors = actual - predicted
    previous = clean.iloc[split - 1:-1].to_numpy()
    actual_returns = actual / previous - 1
    predicted_up = predicted > previous
    strategy_returns = np.where(predicted_up, actual_returns, 0.0)

    return {
        "status": "ok",
        "test_points": int(len(actual)),
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "directional_accuracy": float(np.mean((actual_returns >= 0) == predicted_up)),
        "strategy_return_pct": float((np.prod(1 + strategy_returns) - 1) * 100),
        "buy_hold_return_pct": float((actual[-1] / actual[0] - 1) * 100),
    }
