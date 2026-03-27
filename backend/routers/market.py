from fastapi import APIRouter
from datetime import datetime
import zoneinfo
import db
from models import MarketResponse

router = APIRouter()

@router.get("/market", response_model=MarketResponse)
def get_market():
    conn = db.get_connection()
    try:
        today_wib = datetime.now(zoneinfo.ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d")
        rows = conn.execute(
            "SELECT * FROM ihsg_history WHERE datetime LIKE ? ORDER BY datetime ASC",
            (f"{today_wib}%",),
        ).fetchall()
        history = [dict(r) for r in rows]

        # Fallback: if no data today, use most recent trading day
        if not history:
            rows = conn.execute(
                "SELECT * FROM ihsg_history ORDER BY datetime DESC LIMIT 100"
            ).fetchall()
            if rows:
                last_date = dict(rows[0])["datetime"][:10]
                history = [dict(r) for r in rows if dict(r)["datetime"].startswith(last_date)]
                history.reverse()

        ihsg_price = history[-1]["close"] if history else None
        ihsg_change_pct = None
        if len(history) >= 2:
            first_close = history[0]["close"]
            last_close = history[-1]["close"]
            if first_close and first_close != 0:
                ihsg_change_pct = round((last_close - first_close) / first_close * 100, 4)
        return {
            "ihsg_price": ihsg_price,
            "ihsg_change_pct": ihsg_change_pct,
            "history": history,
        }
    finally:
        conn.close()
