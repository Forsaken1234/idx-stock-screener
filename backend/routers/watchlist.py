from fastapi import APIRouter
import db
from models import WatchlistResponse

router = APIRouter()

@router.get("/watchlist", response_model=WatchlistResponse)
def get_watchlist():
    conn = db.get_connection()
    try:
        return {"tickers": db.get_watchlist(conn)}
    finally:
        conn.close()

@router.post("/watchlist/{ticker}")
def add_to_watchlist(ticker: str):
    conn = db.get_connection()
    try:
        db.add_to_watchlist(conn, ticker.upper())
        return {"status": "added", "ticker": ticker.upper()}
    finally:
        conn.close()

@router.delete("/watchlist/{ticker}")
def remove_from_watchlist(ticker: str):
    conn = db.get_connection()
    try:
        db.remove_from_watchlist(conn, ticker.upper())
        return {"status": "removed", "ticker": ticker.upper()}
    finally:
        conn.close()
