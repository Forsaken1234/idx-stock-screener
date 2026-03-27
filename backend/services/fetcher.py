import logging
import math
from datetime import datetime
import yfinance as yf

logger = logging.getLogger(__name__)


def _safe_float(val) -> float | None:
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def fetch_stock_snapshot(ticker: str) -> dict:
    """
    Fetch latest price, fundamentals, and intraday + daily price history for a ticker.

    Price and history use the v8/finance/chart endpoint (fast_info + history()) which
    is less rate-limited than quoteSummary. Fundamentals (PE, PBV, etc.) use .info
    which hits quoteSummary — falls back to None if rate-limited.

    Returns a dict including a 'closes' list (daily closes for technicals) and
    'bars' list (intraday OHLCV for price_history table).
    Raises on network error — caller handles retry/skip logic.
    """
    yf_ticker = yf.Ticker(f"{ticker}.JK")

    # --- Price via fast_info (v8/finance/chart — not rate-limited like quoteSummary) ---
    fi = yf_ticker.fast_info
    price = _safe_float(fi.get("lastPrice") if hasattr(fi, "get") else getattr(fi, "last_price", None))
    prev_close = _safe_float(fi.get("previousClose") if hasattr(fi, "get") else getattr(fi, "previous_close", None))
    if price is None:
        # fast_info attribute access varies by yfinance version
        try:
            price = _safe_float(fi["lastPrice"])
        except Exception:
            pass
    if prev_close is None:
        try:
            prev_close = _safe_float(fi["previousClose"])
        except Exception:
            pass
    change_pct = None
    if price is not None and prev_close and prev_close != 0:
        change_pct = round((price - prev_close) / prev_close * 100, 4)

    # --- Intraday bars (v8/finance/chart — not rate-limited) ---
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
        # Fallback price from last bar if fast_info didn't give us one
        if price is None and bars:
            price = bars[-1]["close"]

    # --- Daily closes for technicals (v8/finance/chart — not rate-limited) ---
    daily = yf_ticker.history(period="90d", interval="1d")
    closes = []
    if not daily.empty:
        closes = [float(c) for c in daily["Close"].tolist()]
    elif bars:
        closes = [b["close"] for b in bars]

    # --- Fundamentals via .info (quoteSummary — rate-limited, graceful fallback) ---
    name, sector = ticker, "Unknown"
    pe = pbv = roe = eps = market_cap = div_yield = None
    try:
        info = yf_ticker.info or {}
        name = info.get("longName") or info.get("shortName") or ticker
        sector = info.get("sector") or "Unknown"
        pe = _safe_float(info.get("trailingPE"))
        pbv = _safe_float(info.get("priceToBook"))
        roe = _safe_float(info.get("returnOnEquity"))
        eps = _safe_float(info.get("trailingEps"))
        market_cap = _safe_float(info.get("marketCap"))
        div_yield = _safe_float(info.get("dividendYield"))
        # Also get price from info if fast_info failed
        if price is None:
            price = _safe_float(info.get("currentPrice"))
        if prev_close is None:
            prev_close = _safe_float(info.get("previousClose"))
            if price is not None and prev_close and prev_close != 0:
                change_pct = round((price - prev_close) / prev_close * 100, 4)
    except Exception as e:
        logger.warning("Fundamentals fetch failed for %s (will use None): %s", ticker, e)

    return {
        "ticker": ticker,
        "name": name,
        "sector": sector,
        "price": price,
        "change_pct": change_pct,
        "pe": pe,
        "pbv": pbv,
        "roe": roe,
        "eps": eps,
        "market_cap": market_cap,
        "div_yield": div_yield,
        "bars": bars,
        "closes": closes,
        "fetched_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


def fetch_ihsg() -> dict:
    """Fetch IHSG (^JKSE) latest price and today's intraday history."""
    yf_ticker = yf.Ticker("^JKSE")

    # Use history for price — less rate-limited than .info
    hist = yf_ticker.history(period="1d", interval="5m")
    bars = []
    price = None
    if not hist.empty:
        for ts, row in hist.iterrows():
            bars.append({
                "datetime": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                "close": float(row["Close"]),
            })
        price = bars[-1]["close"] if bars else None

    # Try .info for prev_close to compute change_pct
    change_pct = None
    try:
        info = yf_ticker.info or {}
        if price is None:
            price = _safe_float(info.get("currentPrice")) or _safe_float(info.get("regularMarketPrice"))
        prev_close = _safe_float(info.get("previousClose"))
        if price is not None and prev_close and prev_close != 0:
            change_pct = round((price - prev_close) / prev_close * 100, 4)
    except Exception as e:
        logger.warning("IHSG .info failed (change_pct will be None): %s", e)

    return {
        "price": price,
        "change_pct": change_pct,
        "bars": bars,
        "fetched_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
