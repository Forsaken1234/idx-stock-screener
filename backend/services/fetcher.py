import logging
import math
import time
from datetime import datetime, timedelta
import zoneinfo
import httpx

logger = logging.getLogger(__name__)

WIB = zoneinfo.ZoneInfo("Asia/Jakarta")
BASE = "https://www.idx.co.id"

_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.idx.co.id/",
    "X-Requested-With": "XMLHttpRequest",
}


def _safe_float(val) -> float | None:
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _session() -> httpx.Client:
    """Return an httpx Client with IDX session cookies."""
    client = httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=15)
    client.get(f"{BASE}/id")
    return client


def fetch_all_stock_snapshots() -> dict[str, dict]:
    """
    Fetch latest price + daily OHLCV for ALL IDX-listed stocks in ONE API call.
    Tries today's date then walks back up to 5 weekdays to find populated data.
    Returns dict[ticker → {price, change_pct, open, high, low, close, volume, name, market_cap}]
    """
    now_wib = datetime.now(WIB)
    data: dict = {"data": [], "recordsTotal": 0}

    with _session() as client:
        for delta in range(7):
            candidate = now_wib - timedelta(days=delta)
            if candidate.weekday() >= 5:
                continue
            date_str = candidate.strftime("%Y%m%d")
            resp = client.get(
                f"{BASE}/primary/TradingSummary/GetStockSummary",
                params={"date": date_str},
            )
            data = resp.json()
            if data.get("recordsTotal", 0) > 0:
                logger.info("Loaded stock snapshots for %s (%d stocks)", date_str, data["recordsTotal"])
                break

    result: dict[str, dict] = {}
    for row in data.get("data", []):
        ticker = (row.get("StockCode") or "").strip()
        if not ticker:
            continue
        close = _safe_float(row.get("Close"))
        prev = _safe_float(row.get("Previous"))
        change_pct = None
        if close is not None and prev and prev != 0:
            change_pct = round((close - prev) / prev * 100, 4)
        listed_shares = _safe_float(row.get("ListedShares"))
        market_cap = round(close * listed_shares) if close and listed_shares else None
        result[ticker] = {
            "price": close,
            "change_pct": change_pct,
            "open": _safe_float(row.get("OpenPrice")),
            "high": _safe_float(row.get("High")),
            "low": _safe_float(row.get("Low")),
            "close": close,
            "volume": int(row.get("Volume") or 0),
            "name": (row.get("StockName") or "").strip() or ticker,
            "market_cap": market_cap,
        }
    return result


def fetch_stock_history_closes(ticker: str, length: int = 100) -> list[float]:
    """
    Fetch historical daily closes for a ticker (used for technical indicators).
    Returns list in ascending order (oldest first).
    """
    with _session() as client:
        resp = client.get(
            f"{BASE}/primary/ListedCompany/GetTradingInfoSS",
            params={"code": ticker, "start": 0, "length": length},
        )
        data = resp.json()
    replies = data.get("replies", [])
    closes = [
        _safe_float(r.get("Close"))
        for r in replies
        if _safe_float(r.get("Close")) is not None
    ]
    return list(reversed(closes))  # API returns newest-first; reverse to oldest-first


def fetch_all_fundamentals() -> dict[str, dict]:
    """
    Fetch financial ratios (PE, PBV, ROE, EPS, sector) for ALL IDX stocks in one call.
    Tries current month then walks back up to 3 months to find populated data.
    Returns dict[ticker → {pe, pbv, roe, eps, div_yield, sector}]
    Note: roe is returned as decimal (0.204 not 20.4%).
    """
    now_wib = datetime.now(WIB)
    data: dict = {"data": []}

    with _session() as client:
        for delta_months in range(4):
            month = now_wib.month - delta_months
            year = now_wib.year
            while month <= 0:
                month += 12
                year -= 1
            resp = client.get(
                f"{BASE}/primary/DigitalStatistic/GetApiDataPaginated",
                params={
                    "urlName": "LINK_FINANCIAL_DATA_RATIO",
                    "periodYear": year,
                    "periodMonth": month,
                    "periodType": "monthly",
                    "isPrint": "False",
                    "cumulative": "false",
                    "pageSize": 9999,
                    "pageNumber": 1,
                },
            )
            data = resp.json()
            if data.get("data"):
                logger.info("Loaded fundamentals for %d-%02d (%d stocks)", year, month, len(data["data"]))
                break

    result: dict[str, dict] = {}
    for row in data.get("data", []):
        ticker = (row.get("code") or "").strip()
        if not ticker:
            continue
        roe_pct = _safe_float(row.get("roe"))
        result[ticker] = {
            "pe": _safe_float(row.get("per")),
            "pbv": _safe_float(row.get("priceBV")),
            "roe": round(roe_pct / 100, 6) if roe_pct is not None else None,
            "eps": _safe_float(row.get("eps")),
            "div_yield": None,  # not available in IDX financial ratios endpoint
            "sector": (row.get("sector") or "Unknown").strip(),
        }
    return result


def fetch_ihsg() -> dict:
    """
    Fetch IHSG (Composite) current price and today's intraday chart data.
    Returns {price, change_pct, bars, fetched_at}.
    """
    with _session() as client:
        resp = client.get(
            f"{BASE}/primary/helper/GetIndexChart",
            params={"indexCode": "COMPOSITE", "period": "1D"},
        )
        data = resp.json()

    chart_data = data.get("ChartData") or []
    bars = []
    for point in chart_data:
        ts_ms = point.get("Date")
        close = _safe_float(point.get("Close"))
        if ts_ms and close:
            dt = datetime.fromtimestamp(ts_ms / 1000, tz=WIB)
            bars.append({
                "datetime": dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "close": close,
            })

    price = bars[-1]["close"] if bars else None

    # Compute day change: fetch 1W chart to get previous day's close
    change_pct = None
    try:
        with _session() as client:
            resp_w = client.get(
                f"{BASE}/primary/helper/GetIndexChart",
                params={"indexCode": "COMPOSITE", "period": "1W"},
            )
            week_data = resp_w.json()
        week_chart = week_data.get("ChartData") or []
        if week_chart and len(week_chart) >= 2 and price is not None:
            # Find yesterday's last close: all bars not from today
            today_date = datetime.now(WIB).date()
            prev_closes = [
                p["Close"] for p in week_chart
                if datetime.fromtimestamp(p["Date"] / 1000, tz=WIB).date() < today_date
            ]
            if prev_closes:
                prev_close = prev_closes[-1]
                if prev_close and prev_close != 0:
                    change_pct = round((price - prev_close) / prev_close * 100, 4)
    except Exception as e:
        logger.warning("IHSG change_pct calculation failed: %s", e)

    return {
        "price": price,
        "change_pct": change_pct,
        "bars": bars,
        "fetched_at": datetime.now(WIB).strftime("%Y-%m-%dT%H:%M:%S"),
    }
