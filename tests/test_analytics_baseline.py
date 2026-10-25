import pandas as pd
import pytest

from src.analytics_baseline import walk_forward_sma_backtest


def test_walk_forward_baseline_uses_only_prior_prices() -> None:
    result = walk_forward_sma_backtest(pd.Series([10, 11, 12, 13, 14, 15, 16, 17]), window=3, test_fraction=0.25)

    assert result["status"] == "ok"
    assert result["test_points"] == 2
    assert 0.0 <= result["directional_accuracy"] <= 1.0
    assert result["buy_hold_return_pct"] > 0


def test_walk_forward_baseline_validates_inputs() -> None:
    with pytest.raises(ValueError):
        walk_forward_sma_backtest(pd.Series([1, 2, 3]), window=1)
    with pytest.raises(ValueError):
        walk_forward_sma_backtest(pd.Series([1, 2, 3]), test_fraction=1)
