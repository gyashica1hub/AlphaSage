import pytest

from src.forecast_baseline import baseline_forecast


def test_baseline_forecast_returns_interval() -> None:
    result = baseline_forecast([100, 102, 104, 106, 108, 110], window=3)

    assert result["status"] == "ok"
    assert result["forecast"] == pytest.approx(108)
    assert result["lower_bound"] < result["forecast"] < result["upper_bound"]


def test_baseline_forecast_handles_short_history() -> None:
    assert baseline_forecast([100, 101], window=3)["status"] == "insufficient_data"
