import pandas as pd
import pytest

from src.technical_indicators import exponential_moving_average, relative_strength_index, simple_moving_average


def test_moving_averages_use_trailing_windows() -> None:
    prices = pd.Series([10, 12, 14, 16, 18])

    assert simple_moving_average(prices, 3).iloc[-1] == pytest.approx(16)
    assert exponential_moving_average(prices, 3).iloc[-1] > 14
    assert pd.isna(simple_moving_average(prices, 3).iloc[1])


def test_rsi_is_bounded_and_rises_for_positive_series() -> None:
    rsi = relative_strength_index(pd.Series([10, 11, 12, 13, 14, 15]), window=3)

    assert rsi.dropna().between(0, 100).all()
    assert rsi.iloc[-1] == pytest.approx(100)


def test_indicators_validate_windows() -> None:
    with pytest.raises(ValueError):
        simple_moving_average(pd.Series([1, 2]), 0)
