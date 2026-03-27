# IDX Stock Screener — Design Spec

**Date:** 2026-03-27
**Author:** Christopher Ardell
**Status:** Approved

---

## Overview

A personal full-stack web application for screening Indonesian Stock Exchange (IDX) stocks. The tool displays fundamental and technical indicators for LQ45 and IDX30 constituents, with intraday data refresh during market hours.

---

## Goals

- Screen LQ45 and IDX30 stocks by both fundamental and technical criteria
- Refresh data every 5 minutes during IDX market hours (09:00–15:30 WIB, Mon–Fri)
- Provide a full dashboard with charts, metrics, screener table, and watchlist
- Personal use only — no authentication, no multi-user support

---

## Architecture

**Option chosen:** Polling-based (Option A)

```
React (port 5173)
     |
     | REST API — HTTP polling every 5 min via React Query
     |
FastAPI (port 8000)  ← CORSMiddleware allows localhost:5173
     |
     +-- APScheduler (background job, every 5 min during market hours)
     |
     +-- yfinance (price + fundamentals, IHSG index via ^JKSE)
     +-- pandas-ta (technical indicators computed locally)
     +-- IDX website scrape (LQ45/IDX30 constituent lists, weekly)
     |
SQLite (backend/data/screener.db)
```

---

## Backend

### Tech Stack
- **Python 3.11+**
- **FastAPI** — REST API framework
- **APScheduler** — background job scheduler
- **yfinance** — market data (price history, fundamentals, IHSG index)
- **pandas-ta** — technical indicator computation
- **SQLite** — local storage (via Python `sqlite3`)
- **httpx / BeautifulSoup** — IDX website scraping for index membership

### Key Packages (requirements.txt)
```
fastapi
uvicorn
apscheduler
yfinance
pandas-ta
httpx
beautifulsoup4
```

### CORS
FastAPI is configured with `CORSMiddleware` allowing `http://localhost:5173`.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/stocks` | List all stocks with latest snapshot (supports filter params: `index`, `sector`, `rsi_min`, `rsi_max`, `pe_min`, `pe_max`) |
| GET | `/stocks/{ticker}` | Single stock detail + price history array |
| GET | `/watchlist` | Get saved watchlist tickers |
| POST | `/watchlist/{ticker}` | Add ticker to watchlist |
| DELETE | `/watchlist/{ticker}` | Remove ticker from watchlist |
| GET | `/market` | IHSG index latest price + history for dashboard chart |

### Response Shapes

**GET /stocks** — returns array of:
```json
{
  "ticker": "BBCA",
  "name": "Bank Central Asia",
  "sector": "Finance",
  "indices": ["LQ45", "IDX30"],
  "price": 9200,
  "change_pct": 1.2,
  "pe": 23.4, "pbv": 3.1, "roe": 18.5, "eps": 392, "market_cap": 1120000000000, "div_yield": 1.8,
  "rsi": 48.2, "ma20": 9050, "ma50": 8900,
  "macd_line": 45.2, "macd_signal": 38.1, "macd_hist": 7.1,
  "bb_upper": 9420, "bb_mid": 9050, "bb_lower": 8680,
  "fetched_at": "2026-03-27T10:15:00"
}
```

**GET /stocks/{ticker}** — same shape as above, plus:
```json
{
  "price_history": [
    {"datetime": "2026-03-27T09:00:00", "open": 9100, "high": 9250, "low": 9080, "close": 9200, "volume": 4200000}
  ]
}
```

**GET /market**:
```json
{
  "ihsg": {"price": 7284, "change_pct": 0.42},
  "history": [{"datetime": "...", "close": 7284}]
}
```

### Scheduler

- Runs every 5 minutes, Monday–Friday, 09:00–15:30 WIB
- **On startup:** immediately triggers one fetch if current time is within market hours; otherwise waits for next scheduled tick
- **If database is empty on startup:** fetch runs immediately regardless of market hours to seed data
- Fetches yfinance data for all tickers in the `stocks` table (`.JK` suffix)
- Also fetches `^JKSE` (IHSG) on every cycle → stored in a dedicated `ihsg_history` table
- Computes technicals: RSI(14), MA(20), MA(50), MACD, Bollinger Bands
- Stores snapshot to `snapshots` table; appends OHLCV to `price_history`
- On failure for a ticker: logs error, skips, serves last cached snapshot

### Stocks Table Population

1. **Initial seed (on first run):** `idx_members.py` scrapes the IDX website for current LQ45 and IDX30 constituents and inserts them into the `stocks` table. If scraping fails, it falls back to the hardcoded list below.
2. **Weekly refresh:** A separate weekly scheduler job re-scrapes IDX to detect constituent changes (additions/removals). New tickers are inserted; removed tickers are flagged with `active = false` (not deleted, to preserve history).
3. **Ticker metadata** (name, sector) is fetched from `yfinance.Ticker(ticker).info` on first insert.

**Hardcoded fallback LQ45/IDX30 tickers:**
```
LQ45: AALI, ADRO, AKRA, AMMN, AMRT, ANTM, ARTO, ASII, BBCA, BBNI, BBRI, BBTN, BMRI,
      BRIS, BRMS, BRPT, BUKA, CPIN, EMTK, ENRG, ESSA, EXCL, GOTO, HRUM, ICBP,
      INCO, INDF, INKP, INTP, ITMG, JPFA, KLBF, MAPI, MBMA, MDKA, MEDC, MIKA,
      MNCN, PGAS, PTBA, SMGR, TBIG, TLKM, TOWR, UNTR, UNVR

IDX30: AALI, ADRO, AMMN, AMRT, ASII, BBCA, BBNI, BBRI, BMRI, BRIS, BRPT, BUKA,
       EXCL, GOTO, ICBP, INCO, INDF, ITMG, KLBF, MAPI, MDKA, MEDC, MIKA,
       PGAS, PTBA, SMGR, TLKM, TOWR, UNTR, UNVR
```

### Data — Fundamentals Stored
PE ratio, PBV, ROE, EPS, market cap, dividend yield

### Data — Technicals Computed
RSI(14), MA(20), MA(50), MACD (line + signal + histogram), Bollinger Bands (upper/mid/lower)

### Database Schema (SQLite)

**stocks**
- `ticker` TEXT PRIMARY KEY
- `name` TEXT
- `sector` TEXT
- `active` INTEGER DEFAULT 1
- `last_updated` TEXT (ISO datetime)

**stock_indices** (join table for many-to-many)
- `ticker` TEXT
- `index_name` TEXT (e.g. `"LQ45"` or `"IDX30"`)
- PRIMARY KEY (`ticker`, `index_name`)

**snapshots**
- `id` INTEGER PRIMARY KEY
- `ticker` TEXT
- `fetched_at` TEXT (ISO datetime)
- `price`, `change_pct`, `pe`, `pbv`, `roe`, `eps`, `market_cap`, `div_yield`
- `rsi`, `ma20`, `ma50`, `macd_line`, `macd_signal`, `macd_hist`, `bb_upper`, `bb_mid`, `bb_lower`

**price_history**
- `id` INTEGER PRIMARY KEY
- `ticker` TEXT
- `datetime` TEXT (ISO datetime — intraday, one row per 5-min fetch)
- `open`, `high`, `low`, `close`, `volume`
- UNIQUE(`ticker`, `datetime`)

**ihsg_history**
- `id` INTEGER PRIMARY KEY
- `datetime` TEXT
- `close` REAL
- UNIQUE(`datetime`)

**watchlist**
- `ticker` TEXT PRIMARY KEY
- `added_at` TEXT (ISO datetime)

---

## Frontend

### Tech Stack
- **React 18 + Vite**
- **TailwindCSS** — styling
- **lightweight-charts (TradingView)** — candlestick and line charts (Recharts does not have a native candlestick component)
- **React Query** — data fetching + auto-refetch every 5 min

### Layout
Sidebar navigation (persistent left panel) + main content area.

### Pages

| Page | Path | Content |
|------|------|---------|
| Dashboard | `/` | IHSG line chart, market summary stats (gainers count, losers count, oversold RSI<30 count), top movers |
| Screener | `/screener` | Sortable/filterable table. Default state: all active stocks, no filters applied. Filters: PE range, RSI range, sector dropdown, index membership (LQ45 / IDX30 / All) |
| Watchlist | `/watchlist` | Saved stocks with key metrics, quick add/remove button |
| Stock Detail | `/stocks/:ticker` | Candlestick chart (price_history), all fundamentals + technicals, watchlist toggle button |

### Sidebar
- Links to all 4 pages
- Market status badge (Open / Closed) derived from browser local time converted to WIB
- "Last updated: HH:MM" timestamp from most recent snapshot `fetched_at`

### Stale Data Warning
- If `fetched_at` of the most recent snapshot is >10 minutes old, show a yellow banner at the top of the page: "Data may be stale — last updated at [time]"
- Threshold is 10 min (two missed cycles) to avoid false positives from brief scheduler delays

---

## Project Structure

```
personal/
├── backend/
│   ├── main.py              # FastAPI app + scheduler setup + CORS
│   ├── routers/
│   │   ├── stocks.py        # GET /stocks, GET /stocks/{ticker}, GET /market
│   │   └── watchlist.py     # POST/DELETE /watchlist/{ticker}, GET /watchlist
│   ├── services/
│   │   ├── fetcher.py       # yfinance data fetching (stocks + IHSG)
│   │   ├── technicals.py    # pandas-ta calculations
│   │   └── idx_members.py   # LQ45/IDX30 list scraping + hardcoded fallback
│   ├── db.py                # SQLite setup + queries
│   ├── data/                # screener.db lives here
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # Dashboard, Screener, Watchlist, StockDetail
│   │   ├── components/      # Sidebar, StockTable, Chart, MetricCard, StaleWarning
│   │   └── api/             # React Query hooks
│   ├── package.json
│   └── vite.config.js
├── docs/
│   └── superpowers/specs/
│       └── 2026-03-27-idx-stock-screener-design.md
└── README.md
```

---

## Error Handling

- yfinance fetch failure per ticker → skip ticker, log error, serve last cached snapshot
- Scheduler skips fetch cycle when market is closed
- Frontend shows yellow stale data banner if last update >10 min old
- IDX scrape failure → fall back to hardcoded ticker list (see above)
- Cold start with empty DB → scheduler triggers immediate fetch regardless of market hours

---

## Out of Scope

- User authentication
- Multi-user support
- Real-time (sub-minute) data
- Push notifications / alerts
- Mobile app
