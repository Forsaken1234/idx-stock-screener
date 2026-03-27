from pydantic import BaseModel
from typing import Optional


class StockSnapshot(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    indices: list[str] = []
    price: Optional[float] = None
    change_pct: Optional[float] = None
    pe: Optional[float] = None
    pbv: Optional[float] = None
    roe: Optional[float] = None
    eps: Optional[float] = None
    market_cap: Optional[float] = None
    div_yield: Optional[float] = None
    rsi: Optional[float] = None
    ma20: Optional[float] = None
    ma50: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_mid: Optional[float] = None
    bb_lower: Optional[float] = None
    fetched_at: Optional[str] = None


class PriceBar(BaseModel):
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockDetail(StockSnapshot):
    price_history: list[PriceBar] = []


class IHSGBar(BaseModel):
    datetime: str
    close: float


class MarketResponse(BaseModel):
    ihsg_price: Optional[float] = None
    ihsg_change_pct: Optional[float] = None
    history: list[IHSGBar] = []


class WatchlistResponse(BaseModel):
    tickers: list[str]
