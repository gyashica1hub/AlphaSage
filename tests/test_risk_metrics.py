import pytest

from src.risk_metrics import historical_risk_metrics


def test_risk_metrics_capture_drawdown_and_downside() -> None:
    result = historical_risk_metrics([100, 110, 99, 120, 108])

    assert result["status"] == "ok"
    assert result["observations"] == 5
    assert result["max_drawdown"] == pytest.approx(0.1)
    assert result["downside_deviation"] > 0
    assert result["volatility"] > 0


def test_risk_metrics_handle_short_series() -> None:
    assert historical_risk_metrics([100])["status"] == "insufficient_data"
