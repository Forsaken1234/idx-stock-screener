import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

def _mock_ticker_info():
    return {
        "currentPrice": 9200,
        "previousClose": 9090,
        "trailingPE": 23.4,
        "priceToBook": 3.1,
        "returnOnEquity": 0.185,
        "trailingEps": 392.0,
        "marketCap": 1120000000000,
        "dividendYield": 0.018,
    }

def _mock_history_df():
    dates = pd.date_range("2026-03-27 09:00", periods=5, freq="5min")
    return pd.DataFrame({
        "Open":   [9100, 9110, 9120, 9130, 9140],
        "High":   [9150, 9160, 9170, 9180, 9190],
        "Low":    [9080, 9090, 9100, 9110, 9120],
        "Close":  [9120, 9130, 9140, 9150, 9200],
        "Volume": [1000000, 900000, 1100000, 950000, 1200000],
    }, index=dates)

def test_fetch_stock_snapshot_returns_expected_shape():
    from services.fetcher import fetch_stock_snapshot
    mock_ticker = MagicMock()
    mock_ticker.info = _mock_ticker_info()
    mock_ticker.history.return_value = _mock_history_df()

    with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
        result = fetch_stock_snapshot("BBCA")

    assert result["ticker"] == "BBCA"
    assert result["price"] == 9200
    assert result["change_pct"] == pytest.approx((9200 - 9090) / 9090 * 100, rel=0.01)
    assert result["pe"] == 23.4
    assert "closes" in result
    assert len(result["closes"]) == 5

def test_fetch_stock_snapshot_handles_missing_fields():
    from services.fetcher import fetch_stock_snapshot
    mock_ticker = MagicMock()
    mock_ticker.info = {}
    mock_ticker.history.return_value = pd.DataFrame()

    with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
        result = fetch_stock_snapshot("BBCA")

    assert result["ticker"] == "BBCA"
    assert result["price"] is None

def test_fetch_ihsg_returns_close_and_history():
    from services.fetcher import fetch_ihsg
    mock_ticker = MagicMock()
    mock_ticker.info = {"currentPrice": 7284.0, "previousClose": 7254.0}
    mock_ticker.history.return_value = _mock_history_df()

    with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
        result = fetch_ihsg()

    assert result["price"] == pytest.approx(7284.0)
    assert result["change_pct"] == pytest.approx((7284.0 - 7254.0) / 7254.0 * 100, rel=0.01)
    assert len(result["bars"]) == 5
