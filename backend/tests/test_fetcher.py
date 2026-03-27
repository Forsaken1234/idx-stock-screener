import pytest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta
import zoneinfo

WIB = zoneinfo.ZoneInfo("Asia/Jakarta")


def _mock_stock_summary_response():
    """Mock response for GetStockSummary endpoint."""
    return {
        "recordsTotal": 2,
        "data": [
            {
                "StockCode": "BBCA",
                "StockName": "Bank Central Asia Tbk.",
                "Previous": 9090.0,
                "Close": 9200.0,
                "OpenPrice": 9100.0,
                "High": 9250.0,
                "Low": 9080.0,
                "Volume": 1500000,
                "ListedShares": 12345678000,
            },
            {
                "StockCode": "TLKM",
                "StockName": "Telkom Indonesia Tbk.",
                "Previous": 3100.0,
                "Close": 3050.0,
                "OpenPrice": 3110.0,
                "High": 3120.0,
                "Low": 3040.0,
                "Volume": 2000000,
                "ListedShares": 98765432000,
            },
        ],
    }


def _mock_trading_info_response():
    """Mock response for GetTradingInfoSS endpoint (newest-first)."""
    return {
        "replies": [
            {"Close": 9200.0},
            {"Close": 9150.0},
            {"Close": 9100.0},
            {"Close": 9050.0},
            {"Close": 9000.0},
        ]
    }


def _mock_fundamentals_response():
    """Mock response for GetApiDataPaginated LINK_FINANCIAL_DATA_RATIO."""
    return {
        "data": [
            {
                "code": "BBCA",
                "per": 23.4,
                "priceBV": 3.1,
                "roe": 18.5,   # percentage — should be converted to 0.185
                "eps": 392.0,
                "sector": "Finance",
            },
            {
                "code": "TLKM",
                "per": 15.2,
                "priceBV": 2.8,
                "roe": 20.4,
                "eps": 200.0,
                "sector": "Telecommunications",
            },
        ]
    }


def _ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _mock_ihsg_1d_response():
    """Mock response for GetIndexChart COMPOSITE period=1D."""
    today = datetime.now(WIB).replace(hour=9, minute=0, second=0, microsecond=0)
    return {
        "ChartData": [
            {"Date": _ms(today), "Close": 6800.0},
            {"Date": _ms(today.replace(hour=11)), "Close": 6850.0},
            {"Date": _ms(today.replace(hour=13)), "Close": 6900.0},
        ]
    }


def _mock_ihsg_1w_response():
    """Mock response for GetIndexChart COMPOSITE period=1W (includes yesterday)."""
    today = datetime.now(WIB).replace(hour=9, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    return {
        "ChartData": [
            {"Date": _ms(yesterday), "Close": 6750.0},   # yesterday
            {"Date": _ms(today), "Close": 6800.0},        # today
            {"Date": _ms(today.replace(hour=11)), "Close": 6850.0},  # today
        ]
    }


def _make_mock_client(responses: list):
    """Return a mock httpx Client that yields responses in order."""
    mock_client = MagicMock()
    mock_responses = []
    for body in responses:
        r = MagicMock()
        r.json.return_value = body
        mock_responses.append(r)
    mock_client.get.side_effect = mock_responses
    mock_client.__enter__ = lambda self: self
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


# ---------------------------------------------------------------------------
# fetch_all_stock_snapshots
# ---------------------------------------------------------------------------

def test_fetch_all_stock_snapshots_returns_expected_shape():
    from services.fetcher import fetch_all_stock_snapshots

    session_resp = MagicMock()   # GET /id — cookie warmup
    summary_resp = MagicMock()
    summary_resp.json.return_value = _mock_stock_summary_response()

    mock_client = MagicMock()
    mock_client.get.side_effect = [session_resp, summary_resp]
    mock_client.__enter__ = lambda self: self
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("services.fetcher.httpx.Client", return_value=mock_client):
        result = fetch_all_stock_snapshots()

    assert "BBCA" in result
    assert result["BBCA"]["price"] == 9200.0
    assert result["BBCA"]["open"] == 9100.0
    assert result["BBCA"]["high"] == 9250.0
    assert result["BBCA"]["low"] == 9080.0
    assert result["BBCA"]["close"] == 9200.0
    assert result["BBCA"]["volume"] == 1500000
    assert result["BBCA"]["name"] == "Bank Central Asia Tbk."
    assert result["BBCA"]["market_cap"] == round(9200.0 * 12345678000)
    assert result["BBCA"]["change_pct"] == pytest.approx((9200 - 9090) / 9090 * 100, rel=0.01)
    assert "TLKM" in result
    assert result["TLKM"]["change_pct"] == pytest.approx((3050 - 3100) / 3100 * 100, rel=0.01)


def test_fetch_all_stock_snapshots_skips_empty_rows():
    from services.fetcher import fetch_all_stock_snapshots

    session_resp = MagicMock()
    summary_resp = MagicMock()
    summary_resp.json.return_value = {
        "recordsTotal": 1,
        "data": [
            {"StockCode": "", "Close": 100.0},          # empty ticker — skip
            {"StockCode": "BBCA", "Close": 9200.0, "Previous": 9090.0,
             "OpenPrice": 9100.0, "High": 9250.0, "Low": 9080.0,
             "Volume": 1500000, "ListedShares": 1000000,
             "StockName": "BCA"},
        ],
    }

    mock_client = MagicMock()
    mock_client.get.side_effect = [session_resp, summary_resp]
    mock_client.__enter__ = lambda self: self
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("services.fetcher.httpx.Client", return_value=mock_client):
        result = fetch_all_stock_snapshots()

    assert "" not in result
    assert "BBCA" in result


# ---------------------------------------------------------------------------
# fetch_stock_history_closes
# ---------------------------------------------------------------------------

def test_fetch_stock_history_closes_returns_ascending():
    from services.fetcher import fetch_stock_history_closes

    session_resp = MagicMock()
    history_resp = MagicMock()
    history_resp.json.return_value = _mock_trading_info_response()

    mock_client = MagicMock()
    mock_client.get.side_effect = [session_resp, history_resp]
    mock_client.__enter__ = lambda self: self
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("services.fetcher.httpx.Client", return_value=mock_client):
        closes = fetch_stock_history_closes("BBCA")

    # API returns newest-first; fetcher should reverse to oldest-first
    assert closes == [9000.0, 9050.0, 9100.0, 9150.0, 9200.0]


def test_fetch_stock_history_closes_filters_none():
    from services.fetcher import fetch_stock_history_closes

    session_resp = MagicMock()
    history_resp = MagicMock()
    history_resp.json.return_value = {
        "replies": [
            {"Close": 9200.0},
            {"Close": None},        # should be filtered out
            {"Close": "invalid"},   # should be filtered out
            {"Close": 9000.0},
        ]
    }

    mock_client = MagicMock()
    mock_client.get.side_effect = [session_resp, history_resp]
    mock_client.__enter__ = lambda self: self
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("services.fetcher.httpx.Client", return_value=mock_client):
        closes = fetch_stock_history_closes("BBCA")

    assert closes == [9000.0, 9200.0]


# ---------------------------------------------------------------------------
# fetch_all_fundamentals
# ---------------------------------------------------------------------------

def test_fetch_all_fundamentals_returns_expected_shape():
    from services.fetcher import fetch_all_fundamentals

    session_resp = MagicMock()
    fund_resp = MagicMock()
    fund_resp.json.return_value = _mock_fundamentals_response()

    mock_client = MagicMock()
    mock_client.get.side_effect = [session_resp, fund_resp]
    mock_client.__enter__ = lambda self: self
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("services.fetcher.httpx.Client", return_value=mock_client):
        result = fetch_all_fundamentals()

    assert "BBCA" in result
    assert result["BBCA"]["pe"] == pytest.approx(23.4)
    assert result["BBCA"]["pbv"] == pytest.approx(3.1)
    assert result["BBCA"]["roe"] == pytest.approx(0.185)   # converted from 18.5%
    assert result["BBCA"]["eps"] == pytest.approx(392.0)
    assert result["BBCA"]["sector"] == "Finance"
    assert result["BBCA"]["div_yield"] is None

    assert result["TLKM"]["roe"] == pytest.approx(0.204)


def test_fetch_all_fundamentals_skips_empty_tickers():
    from services.fetcher import fetch_all_fundamentals

    session_resp = MagicMock()
    fund_resp = MagicMock()
    fund_resp.json.return_value = {
        "data": [
            {"code": "", "per": 10.0},           # skip
            {"code": "BBCA", "per": 23.4, "priceBV": 3.1, "roe": 18.5, "eps": 392.0, "sector": "Finance"},
        ]
    }

    mock_client = MagicMock()
    mock_client.get.side_effect = [session_resp, fund_resp]
    mock_client.__enter__ = lambda self: self
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("services.fetcher.httpx.Client", return_value=mock_client):
        result = fetch_all_fundamentals()

    assert "" not in result
    assert "BBCA" in result


# ---------------------------------------------------------------------------
# fetch_ihsg
# ---------------------------------------------------------------------------

def test_fetch_ihsg_returns_bars_and_price():
    from services.fetcher import fetch_ihsg

    # fetch_ihsg opens TWO sessions: one for 1D, one for 1W
    session1 = MagicMock()
    resp_1d = MagicMock()
    resp_1d.json.return_value = _mock_ihsg_1d_response()
    session1.get.side_effect = [session1, resp_1d]   # warmup + 1D chart
    session1.__enter__ = lambda self: self
    session1.__exit__ = MagicMock(return_value=False)

    session2 = MagicMock()
    resp_1w = MagicMock()
    resp_1w.json.return_value = _mock_ihsg_1w_response()
    session2.get.side_effect = [session2, resp_1w]   # warmup + 1W chart
    session2.__enter__ = lambda self: self
    session2.__exit__ = MagicMock(return_value=False)

    with patch("services.fetcher.httpx.Client", side_effect=[session1, session2]):
        result = fetch_ihsg()

    assert result["price"] == pytest.approx(6900.0)  # last bar
    assert len(result["bars"]) == 3
    assert "fetched_at" in result
    # change_pct: (6900 - 6750) / 6750 * 100
    assert result["change_pct"] == pytest.approx((6900 - 6750) / 6750 * 100, rel=0.01)


def test_fetch_ihsg_handles_empty_chart():
    from services.fetcher import fetch_ihsg

    session1 = MagicMock()
    resp_1d = MagicMock()
    resp_1d.json.return_value = {"ChartData": []}
    session1.get.side_effect = [session1, resp_1d]
    session1.__enter__ = lambda self: self
    session1.__exit__ = MagicMock(return_value=False)

    session2 = MagicMock()
    resp_1w = MagicMock()
    resp_1w.json.return_value = {"ChartData": []}
    session2.get.side_effect = [session2, resp_1w]
    session2.__enter__ = lambda self: self
    session2.__exit__ = MagicMock(return_value=False)

    with patch("services.fetcher.httpx.Client", side_effect=[session1, session2]):
        result = fetch_ihsg()

    assert result["price"] is None
    assert result["bars"] == []
    assert result["change_pct"] is None
