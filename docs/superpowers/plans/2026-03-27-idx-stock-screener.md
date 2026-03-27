# IDX Stock Screener Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a personal IDX stock screener with FastAPI backend and React frontend that screens LQ45/IDX30 stocks by fundamentals and technicals, refreshing every 5 minutes during IDX market hours.

**Architecture:** FastAPI backend with APScheduler fetches yfinance data every 5 min during IDX market hours (09:00–15:30 WIB Mon–Fri), computes technicals via pandas-ta, stores results in SQLite. React frontend polls via React Query every 5 min, displaying a sidebar-nav dashboard with 4 pages: Dashboard, Screener, Watchlist, Stock Detail. Charts use lightweight-charts (TradingView).

**Tech Stack:** Python 3.11+, FastAPI, APScheduler, yfinance, pandas-ta, SQLite, React 18, Vite, TailwindCSS, lightweight-charts, React Query v5

---

## File Map

```
personal/
├── backend/
│   ├── main.py                  # FastAPI app, CORS, router registration, lifespan
│   ├── db.py                    # SQLite schema creation, connection, all CRUD queries
│   ├── models.py                # Pydantic response models
│   ├── scheduler.py             # APScheduler setup, market hours guard, job definitions
│   ├── routers/
│   │   ├── stocks.py            # GET /stocks, GET /stocks/{ticker}
│   │   ├── market.py            # GET /market
│   │   └── watchlist.py         # GET /watchlist, POST /watchlist/{ticker}, DELETE /watchlist/{ticker}
│   ├── services/
│   │   ├── idx_members.py       # IDX website scrape + hardcoded fallback, seed function
│   │   ├── fetcher.py           # yfinance fetch: stock snapshots + IHSG
│   │   └── technicals.py        # pandas-ta: RSI, MA, MACD, Bollinger computation
│   ├── tests/
│   │   ├── conftest.py          # shared fixtures (in-memory DB, test client)
│   │   ├── test_db.py           # DB schema and CRUD queries
│   │   ├── test_idx_members.py  # fallback list and seed logic
│   │   ├── test_technicals.py   # indicator computation correctness
│   │   ├── test_stocks_router.py
│   │   ├── test_market_router.py
│   │   └── test_watchlist_router.py
│   ├── data/                    # screener.db (gitignored)
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx             # React root, QueryClientProvider, Router
│       ├── App.jsx              # Route definitions
│       ├── api/
│       │   ├── queryClient.js   # React Query client (5-min staleTime)
│       │   ├── stocks.js        # useStocks, useStock hooks
│       │   ├── market.js        # useMarket hook
│       │   └── watchlist.js     # useWatchlist, useAddToWatchlist, useRemoveFromWatchlist
│       ├── components/
│       │   ├── Layout.jsx       # outer wrapper: sidebar + main content
│       │   ├── Sidebar.jsx      # nav links, market status badge, last updated
│       │   ├── StaleWarning.jsx # yellow banner when data > 10 min old
│       │   ├── MetricCard.jsx   # KPI display card
│       │   ├── StockTable.jsx   # sortable/filterable table
│       │   └── Chart.jsx        # lightweight-charts wrapper (line + candlestick modes)
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Screener.jsx
│       │   ├── Watchlist.jsx
│       │   └── StockDetail.jsx
│       └── utils/
│           └── time.js          # WIB conversion, isMarketOpen()
└── .gitignore
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `backend/requirements.txt`
- Create: `frontend/package.json`
- Create: `.gitignore`

- [ ] **Step 1: Create backend folder and requirements.txt**

```bash
mkdir -p /Users/ardell/Documents/personal/backend/data
mkdir -p /Users/ardell/Documents/personal/backend/routers
mkdir -p /Users/ardell/Documents/personal/backend/services
mkdir -p /Users/ardell/Documents/personal/backend/tests
touch /Users/ardell/Documents/personal/backend/routers/__init__.py
touch /Users/ardell/Documents/personal/backend/services/__init__.py
touch /Users/ardell/Documents/personal/backend/tests/__init__.py
```

Create `backend/requirements.txt`:
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
apscheduler==3.10.4
yfinance==0.2.40
pandas-ta==0.3.14b0
httpx==0.27.0
beautifulsoup4==4.12.3
pytest==8.2.0
pytest-asyncio==0.23.6
httpx
```

- [ ] **Step 2: Create Python virtual environment and install dependencies**

```bash
cd /Users/ardell/Documents/personal/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 3: Scaffold React frontend with Vite**

```bash
cd /Users/ardell/Documents/personal
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install @tanstack/react-query lightweight-charts react-router-dom
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom @vitest/coverage-v8
```

- [ ] **Step 4: Configure Tailwind**

Edit `frontend/tailwind.config.js`:
```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

Edit `frontend/src/index.css` (replace contents):
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 5: Configure Vitest in vite.config.js**

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.js'],
  },
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', rewrite: (p) => p.replace(/^\/api/, '') }
    }
  }
})
```

Create `frontend/src/test-setup.js`:
```js
import '@testing-library/jest-dom'
```

- [ ] **Step 6: Create .gitignore**

```
backend/.venv/
backend/data/screener.db
backend/__pycache__/
backend/**/__pycache__/
backend/.pytest_cache/
frontend/node_modules/
frontend/dist/
.superpowers/
```

- [ ] **Step 7: Commit scaffold**

```bash
cd /Users/ardell/Documents/personal
git add .
git commit -m "feat: project scaffold — backend venv, FastAPI deps, React+Vite+Tailwind frontend"
```

---

## Task 2: Database Layer

**Files:**
- Create: `backend/db.py`
- Create: `backend/tests/test_db.py`

- [ ] **Step 1: Write failing tests for DB schema and CRUD**

Create `backend/tests/test_db.py`:
```python
import sqlite3
import pytest
from db import create_schema, get_connection, DB_PATH

@pytest.fixture
def conn(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr("db.DB_PATH", db_file)
    conn = get_connection()
    create_schema(conn)
    yield conn
    conn.close()

def test_schema_creates_all_tables(conn):
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert tables == {"stocks", "stock_indices", "snapshots", "price_history", "ihsg_history", "watchlist"}

def test_insert_and_fetch_stock(conn):
    from db import upsert_stock, get_all_active_stocks
    upsert_stock(conn, ticker="BBCA", name="Bank Central Asia", sector="Finance")
    stocks = get_all_active_stocks(conn)
    assert len(stocks) == 1
    assert stocks[0]["ticker"] == "BBCA"

def test_set_stock_indices(conn):
    from db import upsert_stock, set_stock_indices, get_stock_indices
    upsert_stock(conn, ticker="BBCA", name="Bank Central Asia", sector="Finance")
    set_stock_indices(conn, "BBCA", ["LQ45", "IDX30"])
    indices = get_stock_indices(conn, "BBCA")
    assert set(indices) == {"LQ45", "IDX30"}

def test_upsert_snapshot(conn):
    from db import upsert_stock, upsert_snapshot, get_latest_snapshot
    upsert_stock(conn, ticker="BBCA", name="Bank Central Asia", sector="Finance")
    upsert_snapshot(conn, ticker="BBCA", fetched_at="2026-03-27T10:00:00",
                    price=9200, change_pct=1.2, pe=23.4, pbv=3.1, roe=18.5,
                    eps=392, market_cap=1120000000000, div_yield=1.8,
                    rsi=48.2, ma20=9050, ma50=8900,
                    macd_line=45.2, macd_signal=38.1, macd_hist=7.1,
                    bb_upper=9420, bb_mid=9050, bb_lower=8680)
    snap = get_latest_snapshot(conn, "BBCA")
    assert snap["price"] == 9200
    assert snap["rsi"] == pytest.approx(48.2)

def test_snapshot_unique_constraint(conn):
    from db import upsert_stock, upsert_snapshot
    upsert_stock(conn, ticker="BBCA", name="Bank Central Asia", sector="Finance")
    upsert_snapshot(conn, ticker="BBCA", fetched_at="2026-03-27T10:00:00",
                    price=9200, change_pct=1.2, pe=23.4, pbv=3.1, roe=18.5,
                    eps=392, market_cap=1120000000000, div_yield=1.8,
                    rsi=48.2, ma20=9050, ma50=8900,
                    macd_line=45.2, macd_signal=38.1, macd_hist=7.1,
                    bb_upper=9420, bb_mid=9050, bb_lower=8680)
    # inserting same ticker+fetched_at again should not raise (INSERT OR IGNORE)
    upsert_snapshot(conn, ticker="BBCA", fetched_at="2026-03-27T10:00:00",
                    price=9300, change_pct=2.0, pe=24.0, pbv=3.2, roe=19.0,
                    eps=400, market_cap=1130000000000, div_yield=2.0,
                    rsi=50.0, ma20=9100, ma50=8950,
                    macd_line=46.0, macd_signal=39.0, macd_hist=7.0,
                    bb_upper=9500, bb_mid=9100, bb_lower=8700)
    count = conn.execute("SELECT COUNT(*) FROM snapshots WHERE ticker='BBCA'").fetchone()[0]
    assert count == 1  # still one row, not two

def test_append_price_history(conn):
    from db import upsert_stock, append_price_history, get_price_history
    upsert_stock(conn, ticker="BBCA", name="Bank Central Asia", sector="Finance")
    append_price_history(conn, ticker="BBCA", datetime="2026-03-27T09:00:00",
                         open=9100, high=9250, low=9080, close=9200, volume=4200000)
    history = get_price_history(conn, "BBCA")
    assert len(history) == 1
    assert history[0]["close"] == 9200

def test_price_history_unique_constraint(conn):
    from db import upsert_stock, append_price_history
    upsert_stock(conn, ticker="BBCA", name="Bank Central Asia", sector="Finance")
    append_price_history(conn, ticker="BBCA", datetime="2026-03-27T09:00:00",
                         open=9100, high=9250, low=9080, close=9200, volume=4200000)
    append_price_history(conn, ticker="BBCA", datetime="2026-03-27T09:00:00",
                         open=9100, high=9250, low=9080, close=9200, volume=4200000)
    count = conn.execute("SELECT COUNT(*) FROM price_history WHERE ticker='BBCA'").fetchone()[0]
    assert count == 1

def test_watchlist_add_remove(conn):
    from db import add_to_watchlist, remove_from_watchlist, get_watchlist
    add_to_watchlist(conn, "BBCA")
    assert "BBCA" in get_watchlist(conn)
    remove_from_watchlist(conn, "BBCA")
    assert "BBCA" not in get_watchlist(conn)

def test_ihsg_history_append(conn):
    from db import append_ihsg_history, get_ihsg_history
    append_ihsg_history(conn, datetime="2026-03-27T09:00:00", close=7284.0)
    history = get_ihsg_history(conn)
    assert len(history) == 1
    assert history[0]["close"] == pytest.approx(7284.0)

def test_inactive_stocks_excluded(conn):
    from db import upsert_stock, deactivate_stock, get_all_active_stocks
    upsert_stock(conn, ticker="BBCA", name="Bank Central Asia", sector="Finance")
    upsert_stock(conn, ticker="TLKM", name="Telkom", sector="Telecom")
    deactivate_stock(conn, "TLKM")
    active = get_all_active_stocks(conn)
    tickers = [s["ticker"] for s in active]
    assert "BBCA" in tickers
    assert "TLKM" not in tickers
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd /Users/ardell/Documents/personal/backend
source .venv/bin/activate
pytest tests/test_db.py -v
```

Expected: ImportError or ModuleNotFoundError (db.py not yet created).

- [ ] **Step 3: Implement db.py**

Create `backend/db.py`:
```python
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "screener.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS stocks (
            ticker      TEXT PRIMARY KEY,
            name        TEXT,
            sector      TEXT,
            active      INTEGER DEFAULT 1,
            last_updated TEXT
        );

        CREATE TABLE IF NOT EXISTS stock_indices (
            ticker      TEXT,
            index_name  TEXT,
            PRIMARY KEY (ticker, index_name)
        );

        CREATE TABLE IF NOT EXISTS snapshots (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker      TEXT,
            fetched_at  TEXT,
            price       REAL,
            change_pct  REAL,
            pe          REAL,
            pbv         REAL,
            roe         REAL,
            eps         REAL,
            market_cap  REAL,
            div_yield   REAL,
            rsi         REAL,
            ma20        REAL,
            ma50        REAL,
            macd_line   REAL,
            macd_signal REAL,
            macd_hist   REAL,
            bb_upper    REAL,
            bb_mid      REAL,
            bb_lower    REAL,
            UNIQUE(ticker, fetched_at)
        );

        CREATE TABLE IF NOT EXISTS price_history (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker   TEXT,
            datetime TEXT,
            open     REAL,
            high     REAL,
            low      REAL,
            close    REAL,
            volume   INTEGER,
            UNIQUE(ticker, datetime)
        );

        CREATE TABLE IF NOT EXISTS ihsg_history (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT UNIQUE,
            close    REAL
        );

        CREATE TABLE IF NOT EXISTS watchlist (
            ticker    TEXT PRIMARY KEY,
            added_at  TEXT
        );
    """)
    conn.commit()


def upsert_stock(conn, ticker: str, name: str, sector: str) -> None:
    conn.execute(
        """INSERT INTO stocks (ticker, name, sector, last_updated)
           VALUES (?, ?, ?, datetime('now'))
           ON CONFLICT(ticker) DO UPDATE SET
               name=excluded.name,
               sector=excluded.sector,
               active=1,
               last_updated=excluded.last_updated""",
        (ticker, name, sector),
    )
    conn.commit()


def deactivate_stock(conn, ticker: str) -> None:
    conn.execute("UPDATE stocks SET active=0 WHERE ticker=?", (ticker,))
    conn.commit()


def get_all_active_stocks(conn) -> list[dict]:
    rows = conn.execute("SELECT * FROM stocks WHERE active=1").fetchall()
    return [dict(r) for r in rows]


def set_stock_indices(conn, ticker: str, indices: list[str]) -> None:
    conn.execute("DELETE FROM stock_indices WHERE ticker=?", (ticker,))
    conn.executemany(
        "INSERT OR IGNORE INTO stock_indices (ticker, index_name) VALUES (?, ?)",
        [(ticker, idx) for idx in indices],
    )
    conn.commit()


def get_stock_indices(conn, ticker: str) -> list[str]:
    rows = conn.execute(
        "SELECT index_name FROM stock_indices WHERE ticker=?", (ticker,)
    ).fetchall()
    return [r["index_name"] for r in rows]


def upsert_snapshot(conn, *, ticker, fetched_at, price, change_pct, pe, pbv, roe,
                    eps, market_cap, div_yield, rsi, ma20, ma50,
                    macd_line, macd_signal, macd_hist, bb_upper, bb_mid, bb_lower) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO snapshots
           (ticker, fetched_at, price, change_pct, pe, pbv, roe, eps, market_cap, div_yield,
            rsi, ma20, ma50, macd_line, macd_signal, macd_hist, bb_upper, bb_mid, bb_lower)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (ticker, fetched_at, price, change_pct, pe, pbv, roe, eps, market_cap, div_yield,
         rsi, ma20, ma50, macd_line, macd_signal, macd_hist, bb_upper, bb_mid, bb_lower),
    )
    conn.commit()


def get_latest_snapshot(conn, ticker: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM snapshots WHERE ticker=? ORDER BY fetched_at DESC LIMIT 1",
        (ticker,),
    ).fetchone()
    return dict(row) if row else None


def get_all_latest_snapshots(conn) -> list[dict]:
    rows = conn.execute("""
        SELECT s.* FROM snapshots s
        INNER JOIN (
            SELECT ticker, MAX(fetched_at) AS max_at FROM snapshots GROUP BY ticker
        ) latest ON s.ticker = latest.ticker AND s.fetched_at = latest.max_at
    """).fetchall()
    return [dict(r) for r in rows]


def append_price_history(conn, *, ticker, datetime, open, high, low, close, volume) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO price_history
           (ticker, datetime, open, high, low, close, volume) VALUES (?,?,?,?,?,?,?)""",
        (ticker, datetime, open, high, low, close, volume),
    )
    conn.commit()


def get_price_history(conn, ticker: str, limit: int = 200) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM price_history WHERE ticker=? ORDER BY datetime ASC LIMIT ?",
        (ticker, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def append_ihsg_history(conn, *, datetime: str, close: float) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO ihsg_history (datetime, close) VALUES (?, ?)",
        (datetime, close),
    )
    conn.commit()


def get_ihsg_history(conn, limit: int = 200) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM ihsg_history ORDER BY datetime ASC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def prune_ihsg_history(conn) -> None:
    """Delete ihsg_history rows older than 30 days."""
    conn.execute(
        "DELETE FROM ihsg_history WHERE datetime < datetime('now', '-30 days')"
    )
    conn.commit()


def add_to_watchlist(conn, ticker: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO watchlist (ticker, added_at) VALUES (?, datetime('now'))",
        (ticker,),
    )
    conn.commit()


def remove_from_watchlist(conn, ticker: str) -> None:
    conn.execute("DELETE FROM watchlist WHERE ticker=?", (ticker,))
    conn.commit()


def get_watchlist(conn) -> list[str]:
    rows = conn.execute("SELECT ticker FROM watchlist ORDER BY added_at").fetchall()
    return [r["ticker"] for r in rows]


def get_most_recent_fetch_time(conn) -> str | None:
    row = conn.execute(
        "SELECT MAX(fetched_at) AS t FROM snapshots"
    ).fetchone()
    return row["t"] if row else None
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd /Users/ardell/Documents/personal/backend
source .venv/bin/activate
pytest tests/test_db.py -v
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/ardell/Documents/personal
git add backend/db.py backend/tests/test_db.py
git commit -m "feat: SQLite database layer with full schema and CRUD"
```

---

## Task 3: Pydantic Models

**Files:**
- Create: `backend/models.py`

No TDD needed here — these are data shapes validated by FastAPI at runtime.

- [ ] **Step 1: Create models.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
cd /Users/ardell/Documents/personal
git add backend/models.py
git commit -m "feat: Pydantic response models"
```

---

## Task 4: IDX Members Service

**Files:**
- Create: `backend/services/idx_members.py`
- Create: `backend/tests/test_idx_members.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_idx_members.py`:
```python
from services.idx_members import get_fallback_tickers, get_all_tickers, seed_stocks_table
import db

def test_fallback_lq45_has_expected_tickers():
    tickers = get_fallback_tickers()
    assert "BBCA" in tickers["LQ45"]
    assert "BMRI" in tickers["LQ45"]
    assert len(tickers["LQ45"]) >= 40

def test_fallback_idx30_has_expected_tickers():
    tickers = get_fallback_tickers()
    assert "BBCA" in tickers["IDX30"]
    assert len(tickers["IDX30"]) >= 25

def test_all_tickers_deduped():
    all_tickers = get_all_tickers()
    # no duplicates
    assert len(all_tickers) == len(set(all_tickers))
    # each is a plain ticker (no .JK suffix)
    for t in all_tickers:
        assert "." not in t

def test_seed_stocks_table(tmp_path, monkeypatch):
    import db as db_module
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr("db.DB_PATH", db_file)
    conn = db_module.get_connection()
    db_module.create_schema(conn)
    # seed using fallback (no network call)
    seed_stocks_table(conn, use_scrape=False)
    stocks = db_module.get_all_active_stocks(conn)
    tickers = {s["ticker"] for s in stocks}
    assert "BBCA" in tickers
    assert "TLKM" in tickers
    conn.close()
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd /Users/ardell/Documents/personal/backend
source .venv/bin/activate
pytest tests/test_idx_members.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement idx_members.py**

```python
import logging
import httpx
from bs4 import BeautifulSoup
import yfinance as yf
import db

logger = logging.getLogger(__name__)

_FALLBACK: dict[str, list[str]] = {
    "LQ45": [
        "AALI","ADRO","AKRA","AMMN","AMRT","ANTM","ARTO","ASII","BBCA","BBNI",
        "BBRI","BBTN","BMRI","BRIS","BRMS","BRPT","BUKA","CPIN","EMTK","ENRG",
        "ESSA","EXCL","GOTO","HRUM","ICBP","INCO","INDF","INKP","INTP","ITMG",
        "JPFA","KLBF","MAPI","MBMA","MDKA","MEDC","MIKA","MNCN","PGAS","PTBA",
        "SMGR","TBIG","TLKM","TOWR","UNTR","UNVR",
    ],
    "IDX30": [
        "AALI","ADRO","AMMN","AMRT","ASII","BBCA","BBNI","BBRI","BMRI","BRIS",
        "BRPT","BUKA","EXCL","GOTO","ICBP","INCO","INDF","ITMG","KLBF","MAPI",
        "MDKA","MEDC","MIKA","PGAS","PTBA","SMGR","TLKM","TOWR","UNTR","UNVR",
    ],
}


def get_fallback_tickers() -> dict[str, list[str]]:
    return _FALLBACK


def _scrape_idx_members() -> dict[str, list[str]]:
    """
    Attempt to scrape current LQ45 and IDX30 constituents from IDX website.
    Returns dict like {"LQ45": [...], "IDX30": [...]} or raises on failure.
    """
    url = "https://www.idx.co.id/en/market-data/stocks-data/index-constituent/"
    headers = {"User-Agent": "Mozilla/5.0"}
    result: dict[str, list[str]] = {}
    with httpx.Client(timeout=15) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # IDX page lists index names and their tickers in tables; heuristic parsing
    for index_name in ["LQ45", "IDX30"]:
        tickers = []
        # find table rows containing tickers for this index
        for td in soup.find_all("td"):
            text = td.get_text(strip=True)
            if len(text) >= 4 and len(text) <= 6 and text.isupper():
                tickers.append(text)
        if tickers:
            result[index_name] = list(dict.fromkeys(tickers))  # deduplicate, preserve order
    if not result:
        raise ValueError("No tickers found in scraped page")
    return result


def get_all_tickers(use_scrape: bool = True) -> list[str]:
    """Return deduplicated list of all tickers across LQ45 and IDX30."""
    members = _FALLBACK
    if use_scrape:
        try:
            members = _scrape_idx_members()
        except Exception as e:
            logger.warning("IDX scrape failed, using fallback: %s", e)
    seen: set[str] = set()
    result: list[str] = []
    for tickers in members.values():
        for t in tickers:
            if t not in seen:
                seen.add(t)
                result.append(t)
    return result


def seed_stocks_table(conn, use_scrape: bool = True) -> None:
    """Populate stocks and stock_indices tables from IDX data."""
    members = _FALLBACK
    if use_scrape:
        try:
            members = _scrape_idx_members()
        except Exception as e:
            logger.warning("IDX scrape failed during seed, using fallback: %s", e)

    all_tickers: set[str] = set()
    for tickers in members.values():
        all_tickers.update(tickers)

    for ticker in all_tickers:
        name, sector = ticker, "Unknown"
        try:
            info = yf.Ticker(f"{ticker}.JK").info
            name = info.get("longName") or info.get("shortName") or ticker
            sector = info.get("sector") or "Unknown"
        except Exception:
            pass
        db.upsert_stock(conn, ticker=ticker, name=name, sector=sector)
        indices = [idx for idx, tlist in members.items() if ticker in tlist]
        db.set_stock_indices(conn, ticker, indices)

    logger.info("Seeded %d stocks", len(all_tickers))
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_idx_members.py -v
```

Expected: all 4 tests PASS (seed test uses fallback, no network).

- [ ] **Step 5: Commit**

```bash
cd /Users/ardell/Documents/personal
git add backend/services/idx_members.py backend/tests/test_idx_members.py
git commit -m "feat: IDX members service with scraper and hardcoded fallback"
```

---

## Task 5: Technicals Service

**Files:**
- Create: `backend/services/technicals.py`
- Create: `backend/tests/test_technicals.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_technicals.py`:
```python
import pandas as pd
import pytest
from services.technicals import compute_technicals

def _make_prices(n=60, start=9000, step=10):
    """Generate simple ascending close prices for testing."""
    return [start + i * step for i in range(n)]

def test_returns_all_keys():
    closes = _make_prices(60)
    result = compute_technicals(closes)
    expected_keys = {"rsi", "ma20", "ma50", "macd_line", "macd_signal", "macd_hist",
                     "bb_upper", "bb_mid", "bb_lower"}
    assert expected_keys == set(result.keys())

def test_rsi_in_valid_range():
    closes = _make_prices(60)
    result = compute_technicals(closes)
    if result["rsi"] is not None:
        assert 0 <= result["rsi"] <= 100

def test_ma20_is_average_of_last_20():
    closes = _make_prices(60)
    result = compute_technicals(closes)
    expected_ma20 = sum(closes[-20:]) / 20
    assert result["ma20"] == pytest.approx(expected_ma20, rel=0.001)

def test_ma50_is_average_of_last_50():
    closes = _make_prices(60)
    result = compute_technicals(closes)
    expected_ma50 = sum(closes[-50:]) / 50
    assert result["ma50"] == pytest.approx(expected_ma50, rel=0.001)

def test_short_series_returns_none_gracefully():
    closes = _make_prices(5)  # not enough data
    result = compute_technicals(closes)
    assert result["rsi"] is None
    assert result["ma20"] is None

def test_bollinger_bands_ordering():
    closes = _make_prices(60)
    result = compute_technicals(closes)
    if result["bb_upper"] is not None:
        assert result["bb_upper"] >= result["bb_mid"] >= result["bb_lower"]
```

- [ ] **Step 2: Run test — verify it fails**

```bash
pytest tests/test_technicals.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement technicals.py**

```python
import pandas as pd
import pandas_ta as ta
from typing import Optional

_NONE_RESULT = {
    "rsi": None, "ma20": None, "ma50": None,
    "macd_line": None, "macd_signal": None, "macd_hist": None,
    "bb_upper": None, "bb_mid": None, "bb_lower": None,
}


def compute_technicals(closes: list[float]) -> dict:
    """
    Compute RSI(14), MA(20), MA(50), MACD, Bollinger Bands from a list of close prices.
    Returns a dict with all indicator values. Values are None if not enough data.
    """
    if len(closes) < 20:
        return _NONE_RESULT.copy()

    series = pd.Series(closes, dtype=float)

    def safe(val):
        import math
        if val is None:
            return None
        try:
            f = float(val)
            return None if math.isnan(f) else round(f, 4)
        except (TypeError, ValueError):
            return None

    # RSI
    rsi_series = ta.rsi(series, length=14)
    rsi = safe(rsi_series.iloc[-1]) if rsi_series is not None and len(rsi_series) > 0 else None

    # Moving averages
    ma20 = safe(series.rolling(20).mean().iloc[-1])
    ma50 = safe(series.rolling(50).mean().iloc[-1]) if len(closes) >= 50 else None

    # MACD (default: fast=12, slow=26, signal=9)
    macd_df = ta.macd(series)
    if macd_df is not None and not macd_df.empty:
        macd_line = safe(macd_df.iloc[-1, 0])
        macd_hist = safe(macd_df.iloc[-1, 1])
        macd_signal = safe(macd_df.iloc[-1, 2])
    else:
        macd_line = macd_hist = macd_signal = None

    # Bollinger Bands (length=20, std=2)
    bbands = ta.bbands(series, length=20)
    if bbands is not None and not bbands.empty:
        bb_lower = safe(bbands.iloc[-1, 0])
        bb_mid = safe(bbands.iloc[-1, 1])
        bb_upper = safe(bbands.iloc[-1, 2])
    else:
        bb_lower = bb_mid = bb_upper = None

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
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_technicals.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/ardell/Documents/personal
git add backend/services/technicals.py backend/tests/test_technicals.py
git commit -m "feat: technicals service — RSI, MA, MACD, Bollinger via pandas-ta"
```

---

## Task 6: Fetcher Service

**Files:**
- Create: `backend/services/fetcher.py`
- Create: `backend/tests/test_fetcher.py` (unit tests with mocked yfinance)

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_fetcher.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

def _mock_ticker_info():
    return {
        "currentPrice": 9200,
        "previousClose": 9090,
        "trailingPE": 23.4,
        "priceToBook": 3.1,
        "returnOnEquity": 0.185,
        "trailingEps": 392.0,
        "marketCap": 1120000000000,
        "dividendYield": 0.018,
    }

def _mock_history_df():
    dates = pd.date_range("2026-03-27 09:00", periods=5, freq="5min")
    return pd.DataFrame({
        "Open":   [9100, 9110, 9120, 9130, 9140],
        "High":   [9150, 9160, 9170, 9180, 9190],
        "Low":    [9080, 9090, 9100, 9110, 9120],
        "Close":  [9120, 9130, 9140, 9150, 9200],
        "Volume": [1000000, 900000, 1100000, 950000, 1200000],
    }, index=dates)

def test_fetch_stock_snapshot_returns_expected_shape():
    from services.fetcher import fetch_stock_snapshot
    mock_ticker = MagicMock()
    mock_ticker.info = _mock_ticker_info()
    mock_ticker.history.return_value = _mock_history_df()

    with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
        result = fetch_stock_snapshot("BBCA")

    assert result["ticker"] == "BBCA"
    assert result["price"] == 9200
    assert result["change_pct"] == pytest.approx((9200 - 9090) / 9090 * 100, rel=0.01)
    assert result["pe"] == 23.4
    assert "closes" in result  # raw close prices for technicals
    assert len(result["closes"]) == 5

def test_fetch_stock_snapshot_handles_missing_fields():
    from services.fetcher import fetch_stock_snapshot
    mock_ticker = MagicMock()
    mock_ticker.info = {}  # no data
    mock_ticker.history.return_value = pd.DataFrame()

    with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
        result = fetch_stock_snapshot("BBCA")

    assert result["ticker"] == "BBCA"
    assert result["price"] is None

def test_fetch_ihsg_returns_close_and_history():
    from services.fetcher import fetch_ihsg
    mock_ticker = MagicMock()
    mock_ticker.info = {"currentPrice": 7284.0, "previousClose": 7254.0}
    mock_ticker.history.return_value = _mock_history_df()

    with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
        result = fetch_ihsg()

    assert result["price"] == pytest.approx(7284.0)
    assert result["change_pct"] == pytest.approx((7284.0 - 7254.0) / 7254.0 * 100, rel=0.01)
    assert len(result["bars"]) == 5
```

- [ ] **Step 2: Run test — verify it fails**

```bash
pytest tests/test_fetcher.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement fetcher.py**

```python
import logging
from datetime import datetime, timezone
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)


def _safe_float(val) -> float | None:
    try:
        f = float(val)
        import math
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def fetch_stock_snapshot(ticker: str) -> dict:
    """
    Fetch latest price, fundamentals, and intraday price history for a ticker.
    Returns a dict including a 'closes' list for technicals computation.
    Raises on network error (caller handles retry logic).
    """
    yf_ticker = yf.Ticker(f"{ticker}.JK")
    info = yf_ticker.info or {}

    price = _safe_float(info.get("currentPrice"))
    prev_close = _safe_float(info.get("previousClose"))
    change_pct = None
    if price is not None and prev_close and prev_close != 0:
        change_pct = round((price - prev_close) / prev_close * 100, 4)

    hist = yf_ticker.history(period="1d", interval="5m")
    bars = []
    closes = []
    if not hist.empty:
        for ts, row in hist.iterrows():
            dt_str = ts.strftime("%Y-%m-%dT%H:%M:%S")
            bars.append({
                "datetime": dt_str,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            })
            closes.append(float(row["Close"]))

    # For technicals we also want longer history (60+ days of daily closes)
    # Fetch separate daily history for indicator computation
    daily = yf_ticker.history(period="90d", interval="1d")
    if not daily.empty:
        closes = [float(c) for c in daily["Close"].tolist()]

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
        "bars": bars,      # intraday bars for price_history table
        "closes": closes,  # daily closes for technicals computation
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
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_fetcher.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/ardell/Documents/personal
git add backend/services/fetcher.py backend/tests/test_fetcher.py
git commit -m "feat: fetcher service — yfinance stock and IHSG data fetching"
```

---

## Task 7: Scheduler

**Files:**
- Create: `backend/scheduler.py`

No unit tests for scheduler (APScheduler job orchestration is integration-level). Verified manually in Task 11.

- [ ] **Step 1: Create scheduler.py**

```python
import logging
from datetime import datetime, timezone, timedelta
import zoneinfo
import db
from services.fetcher import fetch_stock_snapshot, fetch_ihsg
from services.technicals import compute_technicals
from services.idx_members import seed_stocks_table, get_all_tickers

logger = logging.getLogger(__name__)

WIB = zoneinfo.ZoneInfo("Asia/Jakarta")


def is_market_open() -> bool:
    """Return True if current WIB time is within IDX market hours."""
    now_wib = datetime.now(WIB)
    if now_wib.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    market_open = now_wib.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now_wib.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now_wib <= market_close


def run_fetch_cycle():
    """Main scheduler job: fetch all tickers, compute technicals, store to DB."""
    if not is_market_open():
        logger.info("Market closed, skipping fetch cycle")
        return

    conn = db.get_connection()
    try:
        tickers = [s["ticker"] for s in db.get_all_active_stocks(conn)]
        if not tickers:
            logger.warning("No tickers in DB, skipping cycle")
            return

        logger.info("Starting fetch cycle for %d tickers", len(tickers))
        for ticker in tickers:
            try:
                data = fetch_stock_snapshot(ticker)
                indicators = compute_technicals(data["closes"])

                # Store intraday bars
                for bar in data["bars"]:
                    db.append_price_history(conn, ticker=ticker, **bar)

                db.upsert_snapshot(
                    conn,
                    ticker=ticker,
                    fetched_at=data["fetched_at"],
                    price=data["price"],
                    change_pct=data["change_pct"],
                    pe=data["pe"],
                    pbv=data["pbv"],
                    roe=data["roe"],
                    eps=data["eps"],
                    market_cap=data["market_cap"],
                    div_yield=data["div_yield"],
                    **indicators,
                )
            except Exception as e:
                logger.error("Failed to fetch %s: %s", ticker, e)

        # Fetch IHSG
        try:
            ihsg = fetch_ihsg()
            for bar in ihsg["bars"]:
                db.append_ihsg_history(conn, datetime=bar["datetime"], close=bar["close"])
        except Exception as e:
            logger.error("Failed to fetch IHSG: %s", e)

        logger.info("Fetch cycle complete")
    finally:
        conn.close()


def run_weekly_member_refresh():
    """Weekly job: re-scrape IDX membership and update stocks table."""
    conn = db.get_connection()
    try:
        seed_stocks_table(conn, use_scrape=True)
        db.prune_ihsg_history(conn)
    except Exception as e:
        logger.error("Weekly refresh failed: %s", e)
    finally:
        conn.close()


def setup_scheduler(app):
    """
    Attach APScheduler to the FastAPI app lifecycle.
    Schedules the 5-min fetch job and weekly refresh job.
    Also seeds DB on cold start if empty.
    """
    from apscheduler.schedulers.background import BackgroundScheduler

    conn = db.get_connection()
    db.create_schema(conn)
    stocks = db.get_all_active_stocks(conn)
    conn.close()

    if not stocks:
        logger.info("Empty DB on startup — seeding stocks table")
        conn = db.get_connection()
        seed_stocks_table(conn, use_scrape=True)
        conn.close()
        # Trigger an immediate fetch regardless of market hours
        logger.info("Cold start: triggering immediate fetch")
        run_fetch_cycle.__wrapped__ = True  # bypass market check for cold start
        _cold_start_fetch()
    elif is_market_open():
        logger.info("Market is open on startup — triggering immediate fetch")
        run_fetch_cycle()

    scheduler = BackgroundScheduler(timezone=WIB)
    scheduler.add_job(run_fetch_cycle, "cron",
                      day_of_week="mon-fri",
                      hour="9-15", minute="*/5",
                      id="fetch_cycle")
    scheduler.add_job(run_weekly_member_refresh, "cron",
                      day_of_week="sun", hour=1,
                      id="weekly_refresh")
    scheduler.start()
    return scheduler


def _cold_start_fetch():
    """Run fetch cycle ignoring market hours (for cold start with empty DB)."""
    conn = db.get_connection()
    try:
        tickers = [s["ticker"] for s in db.get_all_active_stocks(conn)]
        logger.info("Cold start fetch for %d tickers", len(tickers))
        for ticker in tickers[:5]:  # fetch a few to seed data quickly
            try:
                data = fetch_stock_snapshot(ticker)
                indicators = compute_technicals(data["closes"])
                for bar in data["bars"]:
                    db.append_price_history(conn, ticker=ticker, **bar)
                db.upsert_snapshot(
                    conn, ticker=ticker, fetched_at=data["fetched_at"],
                    price=data["price"], change_pct=data["change_pct"],
                    pe=data["pe"], pbv=data["pbv"], roe=data["roe"],
                    eps=data["eps"], market_cap=data["market_cap"],
                    div_yield=data["div_yield"], **indicators,
                )
            except Exception as e:
                logger.error("Cold start fetch failed for %s: %s", ticker, e)
    finally:
        conn.close()
```

- [ ] **Step 2: Commit**

```bash
cd /Users/ardell/Documents/personal
git add backend/scheduler.py
git commit -m "feat: APScheduler setup with market hours guard and cold-start logic"
```

---

## Task 8: FastAPI App + Routers

**Files:**
- Create: `backend/routers/stocks.py`
- Create: `backend/routers/market.py`
- Create: `backend/routers/watchlist.py`
- Create: `backend/main.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_stocks_router.py`
- Create: `backend/tests/test_market_router.py`
- Create: `backend/tests/test_watchlist_router.py`

- [ ] **Step 1: Create test conftest.py**

```python
import pytest
import sqlite3
from fastapi.testclient import TestClient
import db as db_module

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr("db.DB_PATH", db_file)
    conn = db_module.get_connection()
    db_module.create_schema(conn)
    # Seed one stock
    db_module.upsert_stock(conn, ticker="BBCA", name="Bank Central Asia", sector="Finance")
    db_module.set_stock_indices(conn, "BBCA", ["LQ45", "IDX30"])
    db_module.upsert_snapshot(
        conn, ticker="BBCA", fetched_at="2026-03-27T10:00:00",
        price=9200, change_pct=1.2, pe=23.4, pbv=3.1, roe=18.5,
        eps=392, market_cap=1120000000000, div_yield=1.8,
        rsi=48.2, ma20=9050, ma50=8900,
        macd_line=45.2, macd_signal=38.1, macd_hist=7.1,
        bb_upper=9420, bb_mid=9050, bb_lower=8680
    )
    db_module.append_price_history(
        conn, ticker="BBCA", datetime="2026-03-27T09:00:00",
        open=9100, high=9250, low=9080, close=9200, volume=4200000
    )
    db_module.append_ihsg_history(conn, datetime="2026-03-27T09:00:00", close=7284.0)
    conn.close()
    return db_file

@pytest.fixture
def client(test_db):
    from main import app
    return TestClient(app)
```

- [ ] **Step 2: Write failing router tests**

Create `backend/tests/test_stocks_router.py`:
```python
def test_get_stocks_returns_list(client):
    resp = client.get("/stocks")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    stock = data[0]
    assert stock["ticker"] == "BBCA"
    assert stock["price"] == 9200
    assert "LQ45" in stock["indices"]

def test_get_stocks_filter_by_index(client):
    resp = client.get("/stocks?index=LQ45")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_get_stocks_filter_excludes_nonmatch(client):
    resp = client.get("/stocks?index=NONEXISTENT")
    assert resp.status_code == 200
    assert len(resp.json()) == 0

def test_get_stock_detail(client):
    resp = client.get("/stocks/BBCA")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "BBCA"
    assert len(data["price_history"]) == 1

def test_get_stock_detail_not_found(client):
    resp = client.get("/stocks/XXXX")
    assert resp.status_code == 404
```

Create `backend/tests/test_market_router.py`:
```python
def test_get_market(client):
    resp = client.get("/market")
    assert resp.status_code == 200
    data = resp.json()
    assert "ihsg_price" in data
    assert "history" in data
    assert len(data["history"]) == 1
    assert data["history"][0]["close"] == 7284.0
```

Create `backend/tests/test_watchlist_router.py`:
```python
def test_get_empty_watchlist(client):
    resp = client.get("/watchlist")
    assert resp.status_code == 200
    assert resp.json()["tickers"] == []

def test_add_to_watchlist(client):
    resp = client.post("/watchlist/BBCA")
    assert resp.status_code == 200
    resp2 = client.get("/watchlist")
    assert "BBCA" in resp2.json()["tickers"]

def test_remove_from_watchlist(client):
    client.post("/watchlist/BBCA")
    resp = client.delete("/watchlist/BBCA")
    assert resp.status_code == 200
    assert "BBCA" not in client.get("/watchlist").json()["tickers"]
```

- [ ] **Step 3: Run tests — verify they fail**

```bash
pytest tests/test_stocks_router.py tests/test_market_router.py tests/test_watchlist_router.py -v
```

Expected: ImportError or 404s (main.py not yet created).

- [ ] **Step 4: Implement routers**

Create `backend/routers/stocks.py`:
```python
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
            # Check active
            active_row = conn.execute(
                "SELECT active FROM stocks WHERE ticker=?", (ticker,)
            ).fetchone()
            if not active_row or not active_row["active"]:
                continue
            built = _build_snapshot(conn, ticker, snap)
            # Apply filters
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
```

Create `backend/routers/market.py`:
```python
from fastapi import APIRouter
import db
from models import MarketResponse

router = APIRouter()

@router.get("/market", response_model=MarketResponse)
def get_market():
    conn = db.get_connection()
    try:
        history = db.get_ihsg_history(conn)
        ihsg_price = history[-1]["close"] if history else None
        # Compute change_pct from first vs last bar of the day
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
```

Create `backend/routers/watchlist.py`:
```python
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
```

Create `backend/main.py`:
```python
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
```

- [ ] **Step 5: Run router tests — verify they pass**

```bash
pytest tests/test_stocks_router.py tests/test_market_router.py tests/test_watchlist_router.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Run full test suite**

```bash
pytest -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
cd /Users/ardell/Documents/personal
git add backend/
git commit -m "feat: FastAPI app with stocks, market, and watchlist routers"
```

---

## Task 9: Frontend — API Hooks + Query Client

**Files:**
- Create: `frontend/src/api/queryClient.js`
- Create: `frontend/src/api/stocks.js`
- Create: `frontend/src/api/market.js`
- Create: `frontend/src/api/watchlist.js`
- Create: `frontend/src/utils/time.js`

- [ ] **Step 1: Create queryClient.js**

```js
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutes
      refetchInterval: 5 * 60 * 1000, // auto-refetch every 5 min
      retry: 2,
    },
  },
})
```

- [ ] **Step 2: Create time.js utility**

```js
const WIB_OFFSET = 7 * 60 // UTC+7 in minutes

export function toWIB(date = new Date()) {
  const utc = date.getTime() + date.getTimezoneOffset() * 60000
  return new Date(utc + WIB_OFFSET * 60000)
}

export function isMarketOpen() {
  const now = toWIB()
  const day = now.getDay() // 0=Sun, 6=Sat
  if (day === 0 || day === 6) return false
  const hours = now.getHours()
  const minutes = now.getMinutes()
  const total = hours * 60 + minutes
  return total >= 9 * 60 && total <= 15 * 60 + 30
}

export function formatWIBTime(isoString) {
  if (!isoString) return '—'
  const date = new Date(isoString)
  const wib = toWIB(date)
  return wib.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
}

export function isDataStale(fetchedAt, thresholdMinutes = 10) {
  if (!fetchedAt) return false
  const diff = (Date.now() - new Date(fetchedAt).getTime()) / 60000
  return diff > thresholdMinutes
}
```

- [ ] **Step 3: Create API hooks**

Create `frontend/src/api/stocks.js`:
```js
import { useQuery } from '@tanstack/react-query'

const BASE = '/api'

export function useStocks(filters = {}) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => { if (v != null && v !== '') params.set(k, v) })
  const query = params.toString()
  return useQuery({
    queryKey: ['stocks', filters],
    queryFn: () => fetch(`${BASE}/stocks${query ? '?' + query : ''}`).then(r => r.json()),
  })
}

export function useStock(ticker) {
  return useQuery({
    queryKey: ['stock', ticker],
    queryFn: () => fetch(`${BASE}/stocks/${ticker}`).then(r => r.json()),
    enabled: !!ticker,
  })
}
```

Create `frontend/src/api/market.js`:
```js
import { useQuery } from '@tanstack/react-query'

export function useMarket() {
  return useQuery({
    queryKey: ['market'],
    queryFn: () => fetch('/api/market').then(r => r.json()),
  })
}
```

Create `frontend/src/api/watchlist.js`:
```js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export function useWatchlist() {
  return useQuery({
    queryKey: ['watchlist'],
    queryFn: () => fetch('/api/watchlist').then(r => r.json()).then(d => d.tickers),
  })
}

export function useAddToWatchlist() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ticker) => fetch(`/api/watchlist/${ticker}`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  })
}

export function useRemoveFromWatchlist() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ticker) => fetch(`/api/watchlist/${ticker}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  })
}
```

- [ ] **Step 4: Write tests for time.js**

Create `frontend/src/__tests__/time.test.js`:
```js
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { isMarketOpen, isDataStale, formatWIBTime } from '../utils/time'

describe('isMarketOpen', () => {
  it('returns false on weekend', () => {
    // Saturday UTC = Saturday WIB
    vi.setSystemTime(new Date('2026-03-28T10:00:00Z')) // Saturday
    expect(isMarketOpen()).toBe(false)
    vi.useRealTimers()
  })

  it('returns true during market hours on a weekday', () => {
    vi.useFakeTimers()
    // Monday 10:00 WIB = Monday 03:00 UTC
    vi.setSystemTime(new Date('2026-03-30T03:00:00Z'))
    expect(isMarketOpen()).toBe(true)
    vi.useRealTimers()
  })

  it('returns false before market open', () => {
    vi.useFakeTimers()
    // Monday 08:00 WIB = Monday 01:00 UTC
    vi.setSystemTime(new Date('2026-03-30T01:00:00Z'))
    expect(isMarketOpen()).toBe(false)
    vi.useRealTimers()
  })
})

describe('isDataStale', () => {
  it('returns true when fetched_at is 11 minutes ago', () => {
    const elevenMinAgo = new Date(Date.now() - 11 * 60 * 1000).toISOString()
    expect(isDataStale(elevenMinAgo)).toBe(true)
  })

  it('returns false when fetched_at is 5 minutes ago', () => {
    const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString()
    expect(isDataStale(fiveMinAgo)).toBe(false)
  })

  it('returns false for null', () => {
    expect(isDataStale(null)).toBe(false)
  })
})
```

- [ ] **Step 5: Run frontend tests**

```bash
cd /Users/ardell/Documents/personal/frontend
npx vitest run
```

Expected: time.test.js passes.

- [ ] **Step 6: Commit**

```bash
cd /Users/ardell/Documents/personal
git add frontend/src/api/ frontend/src/utils/ frontend/src/__tests__/
git commit -m "feat: React Query hooks and WIB time utilities"
```

---

## Task 10: Frontend — Layout, Sidebar, Shared Components

**Files:**
- Create: `frontend/src/components/Layout.jsx`
- Create: `frontend/src/components/Sidebar.jsx`
- Create: `frontend/src/components/StaleWarning.jsx`
- Create: `frontend/src/components/MetricCard.jsx`
- Create: `frontend/src/components/Chart.jsx`
- Create: `frontend/src/components/StockTable.jsx`

- [ ] **Step 1: Create Layout.jsx**

```jsx
import Sidebar from './Sidebar'
import StaleWarning from './StaleWarning'

export default function Layout({ children, lastFetchedAt }) {
  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      <Sidebar lastFetchedAt={lastFetchedAt} />
      <div className="flex-1 flex flex-col overflow-auto">
        <StaleWarning fetchedAt={lastFetchedAt} />
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create Sidebar.jsx**

```jsx
import { NavLink } from 'react-router-dom'
import { isMarketOpen, formatWIBTime } from '../utils/time'

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/screener', label: 'Screener' },
  { to: '/watchlist', label: 'Watchlist' },
]

export default function Sidebar({ lastFetchedAt }) {
  const open = isMarketOpen()
  return (
    <aside className="w-52 bg-slate-900 flex flex-col shrink-0">
      <div className="p-5 border-b border-slate-800">
        <h1 className="text-indigo-400 font-bold text-lg leading-tight">IDX<br/>Screener</h1>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {links.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `block px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-indigo-600 text-white font-medium'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
              }`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-slate-800 space-y-2">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${open ? 'bg-emerald-400' : 'bg-slate-500'}`} />
          <span className="text-xs text-slate-400">{open ? 'Market Open' : 'Market Closed'}</span>
        </div>
        {lastFetchedAt && (
          <p className="text-xs text-slate-500">
            Updated {formatWIBTime(lastFetchedAt)}
          </p>
        )}
      </div>
    </aside>
  )
}
```

- [ ] **Step 3: Create StaleWarning.jsx**

```jsx
import { isDataStale, formatWIBTime } from '../utils/time'

export default function StaleWarning({ fetchedAt }) {
  if (!isDataStale(fetchedAt)) return null
  return (
    <div className="bg-amber-900/50 border-b border-amber-700 px-6 py-2 text-amber-300 text-sm">
      Data may be stale — last updated at {formatWIBTime(fetchedAt)}
    </div>
  )
}
```

- [ ] **Step 4: Create MetricCard.jsx**

```jsx
export default function MetricCard({ label, value, sub, color = 'text-white' }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <p className="text-xs text-slate-400 uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-xl font-bold ${color}`}>{value ?? '—'}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}
```

- [ ] **Step 5: Create Chart.jsx (lightweight-charts wrapper)**

```jsx
import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

export default function Chart({ data = [], type = 'line', height = 300 }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)
  const seriesRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return
    const chart = createChart(containerRef.current, {
      height,
      layout: { background: { color: '#0f172a' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: '#1e293b' }, horzLines: { color: '#1e293b' } },
      timeScale: { timeVisible: true },
    })
    chartRef.current = chart

    if (type === 'candlestick') {
      seriesRef.current = chart.addCandlestickSeries({
        upColor: '#10b981', downColor: '#ef4444',
        borderUpColor: '#10b981', borderDownColor: '#ef4444',
        wickUpColor: '#10b981', wickDownColor: '#ef4444',
      })
    } else {
      seriesRef.current = chart.addLineSeries({ color: '#6366f1', lineWidth: 2 })
    }

    return () => chart.remove()
  }, [type, height])

  useEffect(() => {
    if (!seriesRef.current || !data.length) return
    if (type === 'candlestick') {
      seriesRef.current.setData(data.map(d => ({
        time: d.datetime.substring(0, 19),
        open: d.open, high: d.high, low: d.low, close: d.close,
      })))
    } else {
      seriesRef.current.setData(data.map(d => ({
        time: d.datetime.substring(0, 19),
        value: d.close,
      })))
    }
    chartRef.current?.timeScale().fitContent()
  }, [data, type])

  return <div ref={containerRef} className="w-full" />
}
```

- [ ] **Step 6: Create StockTable.jsx**

```jsx
import { useState } from 'react'
import { Link } from 'react-router-dom'

const COLUMNS = [
  { key: 'ticker', label: 'Ticker' },
  { key: 'price', label: 'Price', fmt: v => v?.toLocaleString('id-ID') },
  { key: 'change_pct', label: 'Chg%', fmt: v => v != null ? `${v > 0 ? '+' : ''}${v.toFixed(2)}%` : '—', color: v => v > 0 ? 'text-emerald-400' : v < 0 ? 'text-red-400' : '' },
  { key: 'pe', label: 'PE', fmt: v => v?.toFixed(1) },
  { key: 'pbv', label: 'PBV', fmt: v => v?.toFixed(2) },
  { key: 'roe', label: 'ROE%', fmt: v => v != null ? `${(v * 100).toFixed(1)}%` : '—' },
  { key: 'rsi', label: 'RSI', fmt: v => v?.toFixed(1), color: v => v < 30 ? 'text-emerald-400 font-bold' : v > 70 ? 'text-red-400 font-bold' : '' },
  { key: 'market_cap', label: 'Mkt Cap', fmt: v => v != null ? `${(v / 1e12).toFixed(1)}T` : '—' },
]

export default function StockTable({ stocks = [] }) {
  const [sort, setSort] = useState({ key: 'market_cap', dir: 'desc' })

  const sorted = [...stocks].sort((a, b) => {
    const va = a[sort.key], vb = b[sort.key]
    if (va == null) return 1
    if (vb == null) return -1
    return sort.dir === 'asc' ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1)
  })

  const toggleSort = (key) => setSort(s => ({
    key, dir: s.key === key && s.dir === 'desc' ? 'asc' : 'desc'
  }))

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800 bg-slate-900">
            {COLUMNS.map(col => (
              <th
                key={col.key}
                onClick={() => toggleSort(col.key)}
                className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wide cursor-pointer hover:text-slate-200 select-none"
              >
                {col.label}
                {sort.key === col.key && (sort.dir === 'asc' ? ' ↑' : ' ↓')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {sorted.map(stock => (
            <tr key={stock.ticker} className="hover:bg-slate-800/50 transition-colors">
              {COLUMNS.map(col => {
                const val = stock[col.key]
                const displayed = col.fmt ? (col.fmt(val) ?? '—') : (val ?? '—')
                const colorClass = col.color ? col.color(val) : ''
                return (
                  <td key={col.key} className={`px-4 py-3 ${colorClass}`}>
                    {col.key === 'ticker'
                      ? <Link to={`/stocks/${val}`} className="text-indigo-400 hover:text-indigo-300 font-medium">{val}</Link>
                      : displayed
                    }
                  </td>
                )
              })}
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr><td colSpan={COLUMNS.length} className="px-4 py-8 text-center text-slate-500">No stocks match your filters</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 7: Commit**

```bash
cd /Users/ardell/Documents/personal
git add frontend/src/components/
git commit -m "feat: Layout, Sidebar, StaleWarning, MetricCard, Chart, StockTable components"
```

---

## Task 11: Frontend — Pages

**Files:**
- Create: `frontend/src/pages/Dashboard.jsx`
- Create: `frontend/src/pages/Screener.jsx`
- Create: `frontend/src/pages/Watchlist.jsx`
- Create: `frontend/src/pages/StockDetail.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/main.jsx`

- [ ] **Step 1: Create Dashboard.jsx**

```jsx
import { useMarket } from '../api/market'
import { useStocks } from '../api/stocks'
import MetricCard from '../components/MetricCard'
import Chart from '../components/Chart'
import Layout from '../components/Layout'

export default function Dashboard() {
  const { data: market } = useMarket()
  const { data: stocks = [] } = useStocks()

  const gainers = stocks.filter(s => s.change_pct > 0).length
  const losers = stocks.filter(s => s.change_pct < 0).length
  const oversold = stocks.filter(s => s.rsi != null && s.rsi < 30).length
  const lastFetchedAt = stocks[0]?.fetched_at ?? null

  const topMovers = [...stocks]
    .filter(s => s.change_pct != null)
    .sort((a, b) => Math.abs(b.change_pct) - Math.abs(a.change_pct))
    .slice(0, 5)

  return (
    <Layout lastFetchedAt={lastFetchedAt}>
      <h2 className="text-xl font-semibold mb-6">Dashboard</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricCard
          label="IHSG"
          value={market?.ihsg_price?.toLocaleString('id-ID')}
          sub={market?.ihsg_change_pct != null
            ? `${market.ihsg_change_pct > 0 ? '+' : ''}${market.ihsg_change_pct.toFixed(2)}%`
            : undefined}
          color={market?.ihsg_change_pct > 0 ? 'text-emerald-400' : 'text-red-400'}
        />
        <MetricCard label="Gainers" value={gainers} color="text-emerald-400" />
        <MetricCard label="Losers" value={losers} color="text-red-400" />
        <MetricCard label="Oversold (RSI<30)" value={oversold} color="text-amber-400" />
      </div>

      <div className="bg-slate-900 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-medium text-slate-400 mb-3">IHSG Today</h3>
        <Chart data={market?.history ?? []} type="line" height={220} />
      </div>

      <div className="bg-slate-900 rounded-lg p-4">
        <h3 className="text-sm font-medium text-slate-400 mb-3">Top Movers</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-slate-500 border-b border-slate-800">
              <th className="text-left pb-2">Ticker</th>
              <th className="text-left pb-2">Price</th>
              <th className="text-left pb-2">Chg%</th>
            </tr>
          </thead>
          <tbody>
            {topMovers.map(s => (
              <tr key={s.ticker} className="border-b border-slate-800 last:border-0">
                <td className="py-2 text-indigo-400 font-medium">{s.ticker}</td>
                <td className="py-2">{s.price?.toLocaleString('id-ID')}</td>
                <td className={`py-2 ${s.change_pct > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {s.change_pct > 0 ? '+' : ''}{s.change_pct?.toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
```

- [ ] **Step 2: Create Screener.jsx**

```jsx
import { useState } from 'react'
import { useStocks } from '../api/stocks'
import StockTable from '../components/StockTable'
import Layout from '../components/Layout'

export default function Screener() {
  const [filters, setFilters] = useState({})
  const { data: stocks = [], isLoading } = useStocks(filters)
  const lastFetchedAt = stocks[0]?.fetched_at ?? null

  const set = (key, val) => setFilters(f => ({ ...f, [key]: val || undefined }))

  return (
    <Layout lastFetchedAt={lastFetchedAt}>
      <h2 className="text-xl font-semibold mb-6">Screener</h2>

      <div className="flex flex-wrap gap-3 mb-6">
        <select
          onChange={e => set('index', e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
        >
          <option value="">All Indices</option>
          <option value="LQ45">LQ45</option>
          <option value="IDX30">IDX30</option>
        </select>

        <input
          placeholder="PE max"
          type="number"
          onChange={e => set('pe_max', e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm w-24"
        />
        <input
          placeholder="RSI min"
          type="number"
          onChange={e => set('rsi_min', e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm w-24"
        />
        <input
          placeholder="RSI max"
          type="number"
          onChange={e => set('rsi_max', e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm w-24"
        />
      </div>

      {isLoading
        ? <p className="text-slate-400">Loading stocks…</p>
        : <StockTable stocks={stocks} />
      }
    </Layout>
  )
}
```

- [ ] **Step 3: Create Watchlist.jsx**

```jsx
import { Link } from 'react-router-dom'
import { useWatchlist, useRemoveFromWatchlist } from '../api/watchlist'
import { useStocks } from '../api/stocks'
import Layout from '../components/Layout'

export default function Watchlist() {
  const { data: tickers = [] } = useWatchlist()
  const { data: allStocks = [] } = useStocks()
  const remove = useRemoveFromWatchlist()

  const watchlistStocks = allStocks.filter(s => tickers.includes(s.ticker))
  const lastFetchedAt = watchlistStocks[0]?.fetched_at ?? null

  return (
    <Layout lastFetchedAt={lastFetchedAt}>
      <h2 className="text-xl font-semibold mb-6">Watchlist</h2>

      {tickers.length === 0 ? (
        <p className="text-slate-400">
          Your watchlist is empty. Add stocks from the <Link to="/screener" className="text-indigo-400 underline">Screener</Link> or stock detail pages.
        </p>
      ) : (
        <div className="bg-slate-900 rounded-lg border border-slate-800 divide-y divide-slate-800">
          {watchlistStocks.map(stock => (
            <div key={stock.ticker} className="flex items-center justify-between px-5 py-3">
              <div>
                <Link to={`/stocks/${stock.ticker}`} className="text-indigo-400 font-medium hover:text-indigo-300">
                  {stock.ticker}
                </Link>
                <span className="ml-3 text-slate-300">{stock.price?.toLocaleString('id-ID')}</span>
                <span className={`ml-2 text-sm ${stock.change_pct > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {stock.change_pct > 0 ? '+' : ''}{stock.change_pct?.toFixed(2)}%
                </span>
              </div>
              <div className="flex items-center gap-6 text-sm text-slate-400">
                <span>PE {stock.pe?.toFixed(1) ?? '—'}</span>
                <span>RSI {stock.rsi?.toFixed(1) ?? '—'}</span>
                <button
                  onClick={() => remove.mutate(stock.ticker)}
                  className="text-slate-500 hover:text-red-400 transition-colors"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  )
}
```

- [ ] **Step 4: Create StockDetail.jsx**

```jsx
import { useParams } from 'react-router-dom'
import { useStock } from '../api/stocks'
import { useWatchlist, useAddToWatchlist, useRemoveFromWatchlist } from '../api/watchlist'
import Chart from '../components/Chart'
import MetricCard from '../components/MetricCard'
import Layout from '../components/Layout'

function Indicator({ label, value, unit = '' }) {
  return (
    <div className="flex justify-between py-2 border-b border-slate-800 last:border-0">
      <span className="text-slate-400 text-sm">{label}</span>
      <span className="text-slate-100 text-sm font-medium">{value != null ? `${value}${unit}` : '—'}</span>
    </div>
  )
}

export default function StockDetail() {
  const { ticker } = useParams()
  const { data: stock, isLoading } = useStock(ticker)
  const { data: watchlist = [] } = useWatchlist()
  const add = useAddToWatchlist()
  const remove = useRemoveFromWatchlist()
  const inWatchlist = watchlist.includes(ticker)

  if (isLoading) return <Layout><p className="text-slate-400">Loading…</p></Layout>
  if (!stock || stock.detail) return <Layout><p className="text-red-400">Stock not found.</p></Layout>

  return (
    <Layout lastFetchedAt={stock.fetched_at}>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">{ticker}</h2>
          <p className="text-slate-400 text-sm">{stock.name} · {stock.sector}</p>
          <p className="text-sm text-slate-500 mt-1">{stock.indices?.join(', ')}</p>
        </div>
        <button
          onClick={() => inWatchlist ? remove.mutate(ticker) : add.mutate(ticker)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            inWatchlist
              ? 'bg-slate-700 text-slate-300 hover:bg-red-900 hover:text-red-300'
              : 'bg-indigo-600 text-white hover:bg-indigo-500'
          }`}
        >
          {inWatchlist ? '★ Remove from Watchlist' : '☆ Add to Watchlist'}
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <MetricCard
          label="Price"
          value={stock.price?.toLocaleString('id-ID')}
          sub={stock.change_pct != null
            ? `${stock.change_pct > 0 ? '+' : ''}${stock.change_pct.toFixed(2)}%`
            : undefined}
          color={stock.change_pct > 0 ? 'text-emerald-400' : 'text-red-400'}
        />
        <MetricCard label="Market Cap" value={stock.market_cap ? `${(stock.market_cap / 1e12).toFixed(1)}T` : '—'} />
        <MetricCard label="RSI (14)" value={stock.rsi?.toFixed(1)}
          color={stock.rsi < 30 ? 'text-emerald-400' : stock.rsi > 70 ? 'text-red-400' : 'text-white'} />
      </div>

      <div className="bg-slate-900 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-medium text-slate-400 mb-3">Price Chart (Today)</h3>
        <Chart data={stock.price_history ?? []} type="candlestick" height={280} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-slate-900 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Fundamentals</h3>
          <Indicator label="PE Ratio" value={stock.pe?.toFixed(1)} />
          <Indicator label="PBV" value={stock.pbv?.toFixed(2)} />
          <Indicator label="ROE" value={stock.roe != null ? (stock.roe * 100).toFixed(1) : null} unit="%" />
          <Indicator label="EPS" value={stock.eps?.toFixed(0)} />
          <Indicator label="Div Yield" value={stock.div_yield != null ? (stock.div_yield * 100).toFixed(2) : null} unit="%" />
        </div>
        <div className="bg-slate-900 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Technicals</h3>
          <Indicator label="MA (20)" value={stock.ma20?.toLocaleString('id-ID')} />
          <Indicator label="MA (50)" value={stock.ma50?.toLocaleString('id-ID')} />
          <Indicator label="MACD Line" value={stock.macd_line?.toFixed(2)} />
          <Indicator label="MACD Signal" value={stock.macd_signal?.toFixed(2)} />
          <Indicator label="BB Upper" value={stock.bb_upper?.toLocaleString('id-ID')} />
          <Indicator label="BB Lower" value={stock.bb_lower?.toLocaleString('id-ID')} />
        </div>
      </div>
    </Layout>
  )
}
```

- [ ] **Step 5: Wire up App.jsx and main.jsx**

Replace `frontend/src/App.jsx`:
```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Screener from './pages/Screener'
import Watchlist from './pages/Watchlist'
import StockDetail from './pages/StockDetail'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/screener" element={<Screener />} />
        <Route path="/watchlist" element={<Watchlist />} />
        <Route path="/stocks/:ticker" element={<StockDetail />} />
      </Routes>
    </BrowserRouter>
  )
}
```

Replace `frontend/src/main.jsx`:
```jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './api/queryClient'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>
)
```

- [ ] **Step 6: Verify frontend builds without errors**

```bash
cd /Users/ardell/Documents/personal/frontend
npm run build
```

Expected: build succeeds with no errors.

- [ ] **Step 7: Run all frontend tests**

```bash
npx vitest run
```

Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
cd /Users/ardell/Documents/personal
git add frontend/src/
git commit -m "feat: Dashboard, Screener, Watchlist, StockDetail pages with full routing"
```

---

## Task 12: Integration Smoke Test + Final Wiring

**Files:**
- Create: `backend/tests/conftest.py` already exists — no changes
- Verify: end-to-end boot

- [ ] **Step 1: Run full backend test suite**

```bash
cd /Users/ardell/Documents/personal/backend
source .venv/bin/activate
pytest -v --tb=short
```

Expected: all tests PASS.

- [ ] **Step 2: Start backend**

```bash
cd /Users/ardell/Documents/personal/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

Expected: server starts, schema created, scheduler initializes.

- [ ] **Step 3: Verify API responds**

In a new terminal:
```bash
curl http://localhost:8000/stocks
curl http://localhost:8000/market
curl http://localhost:8000/watchlist
```

Expected: all return JSON (stocks may be empty if market is closed and no cold-start data).

- [ ] **Step 4: Start frontend**

```bash
cd /Users/ardell/Documents/personal/frontend
npm run dev
```

Expected: Vite starts on http://localhost:5173

- [ ] **Step 5: Open browser and verify**

Open http://localhost:5173. Verify:
- Sidebar renders with "IDX Screener" title
- Market status badge shows Open/Closed correctly
- Dashboard page loads without JS errors in console
- Navigate to /screener, /watchlist — no crashes

- [ ] **Step 6: Add .gitignore entry for backend data directory**

Verify `backend/data/screener.db` is not tracked:
```bash
git status
```

If `screener.db` appears, confirm `.gitignore` has `backend/data/screener.db`.

- [ ] **Step 7: Final commit**

```bash
cd /Users/ardell/Documents/personal
git add -A
git status  # review — do NOT add screener.db or .venv
git commit -m "feat: complete IDX stock screener — backend + frontend integrated"
```

---

## Running the App

**Backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Open http://localhost:5173
