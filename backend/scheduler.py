import logging
import time
from datetime import datetime
import zoneinfo
import db
from services.fetcher import (
    fetch_all_stock_snapshots,
    fetch_stock_history_closes,
    fetch_all_fundamentals,
    fetch_ihsg,
)
from services.technicals import compute_technicals
from services.idx_members import seed_stocks_table

logger = logging.getLogger(__name__)

WIB = zoneinfo.ZoneInfo("Asia/Jakarta")


def is_market_open() -> bool:
    """Return True if current WIB time is within IDX market hours (Mon-Fri 09:00-15:30)."""
    now_wib = datetime.now(WIB)
    if now_wib.weekday() >= 5:
        return False
    market_open = now_wib.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now_wib.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now_wib <= market_close


def _fetch_and_store(tickers: list[str], label: str = "fetch") -> None:
    """
    Core fetch routine used by both cold-start and regular cycles.
    1. Batch-fetch all prices (1 API call)
    2. Batch-fetch all fundamentals (1 API call)
    3. Per-ticker: fetch history closes → compute technicals → store snapshot
    4. Fetch IHSG
    """
    conn = db.get_connection()
    try:
        logger.info("%s: fetching prices for all tickers", label)
        all_prices = fetch_all_stock_snapshots()

        logger.info("%s: fetching fundamentals for all tickers", label)
        all_fundamentals = fetch_all_fundamentals()

        logger.info("%s: processing %d tickers", label, len(tickers))
        fetched_at = datetime.now(WIB).strftime("%Y-%m-%dT%H:%M:%S")
        today_dt = datetime.now(WIB).strftime("%Y-%m-%dT00:00:00")

        for ticker in tickers:
            try:
                price_data = all_prices.get(ticker, {})
                fund_data = all_fundamentals.get(ticker, {})

                # Update name and sector from fetched data
                name = price_data.get("name") or ticker
                sector = fund_data.get("sector") or "Unknown"
                db.upsert_stock(conn, ticker=ticker, name=name, sector=sector)

                # Fetch per-ticker history for technicals
                closes = fetch_stock_history_closes(ticker)
                indicators = compute_technicals(closes)

                # Store daily OHLCV bar in price_history
                if price_data.get("close"):
                    db.append_price_history(
                        conn, ticker=ticker,
                        datetime=today_dt,
                        open=price_data.get("open"),
                        high=price_data.get("high"),
                        low=price_data.get("low"),
                        close=price_data.get("close"),
                        volume=price_data.get("volume", 0),
                    )

                db.upsert_snapshot(
                    conn,
                    ticker=ticker,
                    fetched_at=fetched_at,
                    price=price_data.get("price"),
                    change_pct=price_data.get("change_pct"),
                    pe=fund_data.get("pe"),
                    pbv=fund_data.get("pbv"),
                    roe=fund_data.get("roe"),
                    eps=fund_data.get("eps"),
                    market_cap=price_data.get("market_cap"),
                    div_yield=fund_data.get("div_yield"),
                    **indicators,
                )
            except Exception as e:
                logger.error("%s failed for %s: %s", label, ticker, e)
            time.sleep(1)

        # IHSG
        try:
            ihsg = fetch_ihsg()
            for bar in ihsg["bars"]:
                db.append_ihsg_history(conn, datetime=bar["datetime"], close=bar["close"])
            logger.info("%s: IHSG fetched, %d bars", label, len(ihsg["bars"]))
        except Exception as e:
            logger.error("%s: IHSG fetch failed: %s", label, e)

        logger.info("%s complete", label)
    finally:
        conn.close()


def run_fetch_cycle(force: bool = False) -> None:
    """Scheduled job: fetch all active tickers. Skips when market is closed unless force=True."""
    if not force and not is_market_open():
        logger.info("Market closed, skipping fetch cycle")
        return
    conn = db.get_connection()
    tickers = [s["ticker"] for s in db.get_all_active_stocks(conn)]
    conn.close()
    if not tickers:
        logger.warning("No tickers in DB, skipping cycle")
        return
    _fetch_and_store(tickers, label="fetch_cycle")


def run_weekly_member_refresh() -> None:
    """Weekly job: re-scrape IDX membership and prune old IHSG history."""
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
    Initialize scheduler on startup.
    - Seeds stocks table if DB is empty
    - Always triggers one fetch on startup to ensure data is fresh
    - Schedules 5-min fetch during market hours + weekly refresh
    """
    from apscheduler.schedulers.background import BackgroundScheduler

    conn = db.get_connection()
    db.create_schema(conn)
    stocks = db.get_all_active_stocks(conn)
    has_snapshots = bool(db.get_most_recent_fetch_time(conn))
    conn.close()

    if not stocks:
        logger.info("Empty DB on startup — seeding stocks table")
        conn = db.get_connection()
        seed_stocks_table(conn, use_scrape=True)
        conn.close()

    conn = db.get_connection()
    tickers = [s["ticker"] for s in db.get_all_active_stocks(conn)]
    conn.close()

    if tickers:
        logger.info("Startup fetch — refreshing data (market %s)", "open" if is_market_open() else "closed")
        _fetch_and_store(tickers, label="startup_fetch")
    else:
        logger.warning("No tickers found after seeding — skipping startup fetch")

    scheduler = BackgroundScheduler(timezone=WIB)
    scheduler.add_job(
        run_fetch_cycle, "cron",
        day_of_week="mon-fri",
        hour="9-15", minute="*/5",
        id="fetch_cycle",
    )
    scheduler.add_job(
        run_weekly_member_refresh, "cron",
        day_of_week="sun", hour=1,
        id="weekly_refresh",
    )
    scheduler.start()
    return scheduler
