import math
import pandas as pd
import pandas_ta as ta


def compute_technicals(closes: list[float]) -> dict:
    """
    Compute technical indicators from a list of close prices.

    Returns a dict with keys:
        rsi, ma20, ma50, macd_line, macd_signal, macd_hist,
        bb_upper, bb_mid, bb_lower

    Any indicator that cannot be computed due to insufficient data is None.
    All non-None values are rounded to 4 decimal places.
    """
    none_result = {
        "rsi": None,
        "ma20": None,
        "ma50": None,
        "macd_line": None,
        "macd_signal": None,
        "macd_hist": None,
        "bb_upper": None,
        "bb_mid": None,
        "bb_lower": None,
    }

    if len(closes) < 20:
        return none_result

    s = pd.Series(closes, dtype=float)

    def _val(x):
        """Return rounded float or None if NaN/None."""
        if x is None:
            return None
        try:
            if math.isnan(float(x)):
                return None
            return round(float(x), 4)
        except (TypeError, ValueError):
            return None

    # RSI(14)
    rsi = None
    try:
        rsi_s = ta.rsi(s, length=14)
        rsi = _val(rsi_s.iloc[-1])
    except Exception:
        pass

    # MA20 and MA50
    ma20 = _val(s.tail(20).mean()) if len(closes) >= 20 else None
    ma50 = _val(s.tail(50).mean()) if len(closes) >= 50 else None

    # MACD (fast=12, slow=26, signal=9)
    macd_line = macd_signal = macd_hist = None
    try:
        macd_df = ta.macd(s, fast=12, slow=26, signal=9)
        if macd_df is not None and not macd_df.empty:
            last = macd_df.iloc[-1]
            macd_line = _val(last.get("MACD_12_26_9"))
            macd_hist = _val(last.get("MACDh_12_26_9"))
            macd_signal = _val(last.get("MACDs_12_26_9"))
    except Exception:
        pass

    # Bollinger Bands (length=20, std=2)
    bb_upper = bb_mid = bb_lower = None
    try:
        bb_df = ta.bbands(s, length=20, std=2)
        if bb_df is not None and not bb_df.empty:
            last = bb_df.iloc[-1]
            # Column names in pandas-ta 0.4.x: BBL_20_2.0_2.0, BBM_20_2.0_2.0, BBU_20_2.0_2.0
            for col in bb_df.columns:
                if col.startswith("BBL_"):
                    bb_lower = _val(last[col])
                elif col.startswith("BBM_"):
                    bb_mid = _val(last[col])
                elif col.startswith("BBU_"):
                    bb_upper = _val(last[col])
    except Exception:
        pass

    return {
        "rsi": rsi,
        "ma20": ma20,
        "ma50": ma50,
        "macd_line": macd_line,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "bb_upper": bb_upper,
        "bb_mid": bb_mid,
        "bb_lower": bb_lower,
    }
