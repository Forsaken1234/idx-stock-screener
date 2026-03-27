import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import db
from routers import stocks, market, watchlist
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)

_scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    conn = db.get_connection()
    db.create_schema(conn)
    conn.close()
    _scheduler = setup_scheduler(app)
    yield
    if _scheduler:
        _scheduler.shutdown()

app = FastAPI(title="IDX Stock Screener", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router)
app.include_router(market.router)
app.include_router(watchlist.router)
