import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


def _mock_fast_info(last_price=9200, previous_close=9090):
    """Mock fast_info object with attribute-style access."""
    fi = MagicMock()
    fi.last_price = last_price
    fi.previous_close = previous_close
    # Also support dict-style access used in fetcher
    fi.__getitem__ = lambda self, key: {
        "lastPrice": last_price, "previousClose": previous_close
    }[key]
    fi.get = lambda key, default=None: {
        "lastPrice": last_price, "previousClose": previous_close
    }.get(key, default)
    fi.__contains__ = lambda self, key: key in {"lastPrice", "previousClose"}
    return fi


def _mock_ticker_info():
    return {
        "trailingPE": 23.4,
        "priceToBook": 3.1,
        "returnOnEquity": 0.185,
        "trailingEps": 392.0,
        "marketCap": 1120000000000,
        "dividendYield": 0.018,
        "longName": "Bank Central Asia",
        "sector": "Finance",
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
    mock_ticker.fast_info = _mock_fast_info(last_price=9200, previous_close=9090)
    mock_ticker.info = _mock_ticker_info()
    mock_ticker.history.return_value = _mock_history_df()

    with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
        result = fetch_stock_snapshot("BBCA")

    assert result["ticker"] == "BBCA"
    assert result["price"] == 9200
    assert result["change_pct"] == pytest.approx((9200 - 9090) / 9090 * 100, rel=0.01)
    assert result["pe"] == 23.4
    assert result["name"] == "Bank Central Asia"
    assert result["sector"] == "Finance"
    assert "closes" in result
    assert len(result["closes"]) == 5


def test_fetch_stock_snapshot_handles_missing_fields():
    from services.fetcher import fetch_stock_snapshot
    mock_ticker = MagicMock()
    # fast_info with no price — __getitem__ raises so fallback also fails
    fi = MagicMock()
    fi.last_price = None
    fi.previous_close = None
    fi.get = lambda key, default=None: default
    fi.__getitem__ = MagicMock(side_effect=KeyError)
    mock_ticker.fast_info = fi
    mock_ticker.info = {}
    mock_ticker.history.return_value = pd.DataFrame()

    with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
        result = fetch_stock_snapshot("BBCA")

    assert result["ticker"] == "BBCA"
    assert result["price"] is None


def test_fetch_ihsg_returns_close_and_history():
    from services.fetcher import fetch_ihsg
    mock_ticker = MagicMock()
    mock_ticker.info = {"previousClose": 7254.0}
    mock_ticker.history.return_value = _mock_history_df()

    with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
        result = fetch_ihsg()

    # Price comes from last bar close (9200 from mock history)
    assert result["price"] == pytest.approx(9200.0)
    assert len(result["bars"]) == 5
