from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import db
from models import StockSnapshot, StockDetail, PriceBar

router = APIRouter()

def _build_snapshot(conn, ticker: str, snap: dict) -> dict:
    indices = db.get_stock_indices(conn, ticker)
    stock_row = conn.execute(
        "SELECT name, sector FROM stocks WHERE ticker=?", (ticker,)
    ).fetchone()
    return {
        "ticker": ticker,
        "name": stock_row["name"] if stock_row else None,
        "sector": stock_row["sector"] if stock_row else None,
        "indices": indices,
        **{k: snap.get(k) for k in [
            "price", "change_pct", "pe", "pbv", "roe", "eps", "market_cap", "div_yield",
            "rsi", "ma20", "ma50", "macd_line", "macd_signal", "macd_hist",
            "bb_upper", "bb_mid", "bb_lower", "fetched_at"
        ]},
    }

@router.get("/stocks", response_model=list[StockSnapshot])
def list_stocks(
    index: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    rsi_min: Optional[float] = Query(None),
    rsi_max: Optional[float] = Query(None),
    pe_min: Optional[float] = Query(None),
    pe_max: Optional[float] = Query(None),
):
    conn = db.get_connection()
    try:
        snapshots = db.get_all_latest_snapshots(conn)
        result = []
        for snap in snapshots:
            ticker = snap["ticker"]
            active_row = conn.execute(
                "SELECT active FROM stocks WHERE ticker=?", (ticker,)
            ).fetchone()
            if not active_row or not active_row["active"]:
                continue
            built = _build_snapshot(conn, ticker, snap)
            if index and index not in built["indices"]:
                continue
            if sector and built["sector"] != sector:
                continue
            if rsi_min is not None and (built["rsi"] is None or built["rsi"] < rsi_min):
                continue
            if rsi_max is not None and (built["rsi"] is None or built["rsi"] > rsi_max):
                continue
            if pe_min is not None and (built["pe"] is None or built["pe"] < pe_min):
                continue
            if pe_max is not None and (built["pe"] is None or built["pe"] > pe_max):
                continue
            result.append(built)
        return result
    finally:
        conn.close()


@router.get("/stocks/{ticker}", response_model=StockDetail)
def get_stock(ticker: str):
    conn = db.get_connection()
    try:
        snap = db.get_latest_snapshot(conn, ticker)
        if not snap:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")
        built = _build_snapshot(conn, ticker, snap)
        history = db.get_price_history(conn, ticker)
        built["price_history"] = history
        return built
    finally:
        conn.close()
