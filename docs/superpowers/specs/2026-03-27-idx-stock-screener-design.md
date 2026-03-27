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
FastAPI (port 8000)
     |
     +-- APScheduler (background job, every 5 min during market hours)
     |
     +-- yfinance (price + fundamentals)
     +-- pandas-ta (technical indicators computed locally)
     +-- IDX website scrape (LQ45/IDX30 constituent lists)
     |
SQLite (backend/data/screener.db)
```

---

## Backend

### Tech Stack
- **Python 3.11+**
- **FastAPI** — REST API framework
- **APScheduler** — background job scheduler
- **yfinance** — market data (price history, fundamentals)
- **pandas-ta** — technical indicator computation
- **SQLite** — local storage (via Python `sqlite3`)
- **httpx / BeautifulSoup** — IDX website scraping for index membership

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/stocks` | List all stocks with latest snapshot (supports filter params) |
| GET | `/stocks/{ticker}` | Single stock detail + price history |
| GET | `/watchlist` | Get saved watchlist tickers |
| POST | `/watchlist` | Add or remove a ticker from watchlist |

### Scheduler

- Runs every 5 minutes, Monday–Friday, 09:00–15:30 WIB
- Fetches yfinance data for all LQ45/IDX30 tickers (`.JK` suffix)
- Computes technicals: RSI(14), MA(20), MA(50), MACD, Bollinger Bands
- Stores snapshot to `snapshots` table; appends OHLCV to `price_history`
- On failure for a ticker: logs error, skips, serves last cached data

### Data — Fundamentals Stored
PE ratio, PBV, ROE, EPS, market cap, dividend yield

### Data — Technicals Computed
RSI(14), MA(20), MA(50), MACD (line + signal + histogram), Bollinger Bands (upper/mid/lower)

### Database Schema (SQLite)

**stocks** — ticker, name, sector, index_membership (LQ45/IDX30), last_updated

**snapshots** — id, ticker, fetched_at, price, change_pct, pe, pbv, roe, eps, market_cap, div_yield, rsi, ma20, ma50, macd_line, macd_signal, macd_hist, bb_upper, bb_mid, bb_lower

**price_history** — id, ticker, date, open, high, low, close, volume

**watchlist** — ticker, added_at

---

## Frontend

### Tech Stack
- **React 18 + Vite**
- **TailwindCSS** — styling
- **Recharts** — charts (line chart, candlestick)
- **React Query** — data fetching + auto-refetch every 5 min

### Layout
Sidebar navigation (persistent left panel) + main content area.

### Pages

| Page | Path | Content |
|------|------|---------|
| Dashboard | `/` | IHSG index chart, market summary stats (gainers, losers, oversold count), top movers |
| Screener | `/screener` | Sortable/filterable table — filter by PE range, RSI range, sector, index membership |
| Watchlist | `/watchlist` | Saved stocks with key metrics, quick add/remove |
| Stock Detail | `/stocks/:ticker` | Candlestick chart, all fundamentals + technicals, watchlist toggle |

### Sidebar
- Links to all 4 pages
- Market status badge (Open / Closed) based on current WIB time
- "Last updated" timestamp

### Data Freshness
- React Query refetches every 5 min automatically
- If last update is >10 min old, show a stale data warning indicator

---

## Project Structure

```
personal/
├── backend/
│   ├── main.py              # FastAPI app + scheduler setup
│   ├── routers/
│   │   ├── stocks.py        # GET /stocks, GET /stocks/{ticker}
│   │   └── watchlist.py     # GET/POST /watchlist
│   ├── services/
│   │   ├── fetcher.py       # yfinance data fetching
│   │   ├── technicals.py    # pandas-ta calculations
│   │   └── idx_members.py   # LQ45/IDX30 list scraping
│   ├── db.py                # SQLite setup + queries
│   ├── data/                # screener.db lives here
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # Dashboard, Screener, Watchlist, StockDetail
│   │   ├── components/      # Sidebar, StockTable, Chart, MetricCard
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
- Frontend shows stale data indicator if last update >10 min old
- IDX scrape failure → fall back to hardcoded LQ45/IDX30 ticker list

---

## Out of Scope

- User authentication
- Multi-user support
- Real-time (sub-minute) data
- Push notifications / alerts
- Mobile app
