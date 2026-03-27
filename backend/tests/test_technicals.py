import pandas as pd
import pytest
from services.technicals import compute_technicals

def _make_prices(n=60, start=9000, step=10):
    """Generate simple ascending close prices for testing."""
    return [start + i * step for i in range(n)]

def test_returns_all_keys():
    closes = _make_prices(60)
    result = compute_technicals(closes)
    expected_keys = {"rsi", "ma20", "ma50", "macd_line", "macd_signal", "macd_hist",
                     "bb_upper", "bb_mid", "bb_lower"}
    assert expected_keys == set(result.keys())

def test_rsi_in_valid_range():
    closes = _make_prices(60)
    result = compute_technicals(closes)
    assert result["rsi"] is not None, "RSI should be computable with 60 data points"
    assert 0 <= result["rsi"] <= 100

def test_ma20_is_average_of_last_20():
    closes = _make_prices(60)
    result = compute_technicals(closes)
    expected_ma20 = sum(closes[-20:]) / 20
    assert result["ma20"] == pytest.approx(expected_ma20, rel=0.001)

def test_ma50_is_average_of_last_50():
    closes = _make_prices(60)
    result = compute_technicals(closes)
    expected_ma50 = sum(closes[-50:]) / 50
    assert result["ma50"] == pytest.approx(expected_ma50, rel=0.001)

def test_short_series_returns_none_gracefully():
    closes = _make_prices(5)  # not enough data
    result = compute_technicals(closes)
    assert result["rsi"] is None
    assert result["ma20"] is None

def test_bollinger_bands_ordering():
    closes = _make_prices(60)
    result = compute_technicals(closes)
    if result["bb_upper"] is not None:
        assert result["bb_upper"] >= result["bb_mid"] >= result["bb_lower"]
