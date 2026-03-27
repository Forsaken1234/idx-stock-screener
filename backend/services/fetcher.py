import logging
from datetime import datetime
import yfinance as yf

logger = logging.getLogger(__name__)


def _safe_float(val) -> float | None:
    try:
        import math
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def fetch_stock_snapshot(ticker: str) -> dict:
    """
    Fetch latest price, fundamentals, and intraday + daily price history for a ticker.
    Returns a dict including a 'closes' list (daily closes for technicals) and
    'bars' list (intraday OHLCV for price_history table).
    Raises on network error — caller handles retry/skip logic.
    """
    yf_ticker = yf.Ticker(f"{ticker}.JK")
    info = yf_ticker.info or {}

    price = _safe_float(info.get("currentPrice"))
    prev_close = _safe_float(info.get("previousClose"))
    change_pct = None
    if price is not None and prev_close and prev_close != 0:
        change_pct = round((price - prev_close) / prev_close * 100, 4)

    # Intraday bars for price_history table
    intraday = yf_ticker.history(period="1d", interval="5m")
    bars = []
    if not intraday.empty:
        for ts, row in intraday.iterrows():
            bars.append({
                "datetime": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            })

    # Daily closes for technicals (need 60+ days)
    daily = yf_ticker.history(period="90d", interval="1d")
    closes = []
    if not daily.empty:
        closes = [float(c) for c in daily["Close"].tolist()]
    elif bars:
        # Fallback: use intraday closes if no daily data
        closes = [b["close"] for b in bars]

    return {
        "ticker": ticker,
        "price": price,
        "change_pct": change_pct,
        "pe": _safe_float(info.get("trailingPE")),
        "pbv": _safe_float(info.get("priceToBook")),
        "roe": _safe_float(info.get("returnOnEquity")),
        "eps": _safe_float(info.get("trailingEps")),
        "market_cap": _safe_float(info.get("marketCap")),
        "div_yield": _safe_float(info.get("dividendYield")),
        "bars": bars,
        "closes": closes,
        "fetched_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


def fetch_ihsg() -> dict:
    """Fetch IHSG (^JKSE) latest price and today's intraday history."""
    yf_ticker = yf.Ticker("^JKSE")
    info = yf_ticker.info or {}

    price = _safe_float(info.get("currentPrice")) or _safe_float(info.get("regularMarketPrice"))
    prev_close = _safe_float(info.get("previousClose"))
    change_pct = None
    if price is not None and prev_close and prev_close != 0:
        change_pct = round((price - prev_close) / prev_close * 100, 4)

    hist = yf_ticker.history(period="1d", interval="5m")
    bars = []
    if not hist.empty:
        for ts, row in hist.iterrows():
            bars.append({
                "datetime": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                "close": float(row["Close"]),
            })

    return {
        "price": price,
        "change_pct": change_pct,
        "bars": bars,
        "fetched_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
