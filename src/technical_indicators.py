"""Small, dependency-light technical indicators for research features."""

from __future__ import annotations

import pandas as pd


def simple_moving_average(prices: pd.Series, window: int = 20) -> pd.Series:
    """Return a rolling arithmetic mean without peeking into future prices."""
    if window < 1:
        raise ValueError("window must be positive")
    return prices.astype(float).rolling(window=window, min_periods=window).mean()


def exponential_moving_average(prices: pd.Series, window: int = 20) -> pd.Series:
    """Return an exponentially weighted moving average."""
    if window < 1:
        raise ValueError("window must be positive")
    return prices.astype(float).ewm(span=window, adjust=False, min_periods=window).mean()


def relative_strength_index(prices: pd.Series, window: int = 14) -> pd.Series:
    """Return Wilder-style RSI values on a 0–100 scale."""
    if window < 1:
        raise ValueError("window must be positive")
    changes = prices.astype(float).diff()
    gains = changes.clip(lower=0)
    losses = -changes.clip(upper=0)
    average_gain = gains.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    average_loss = losses.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    relative_strength = average_gain / average_loss.where(average_loss != 0)
    return (100 - (100 / (1 + relative_strength))).where(average_loss != 0, 100.0)
