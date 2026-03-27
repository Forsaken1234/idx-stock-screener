import logging
import time
from datetime import datetime
import zoneinfo
import db
from services.fetcher import fetch_stock_snapshot, fetch_ihsg
from services.technicals import compute_technicals
from services.idx_members import seed_stocks_table

logger = logging.getLogger(__name__)

WIB = zoneinfo.ZoneInfo("Asia/Jakarta")


def is_market_open() -> bool:
    """Return True if current WIB time is within IDX market hours (Mon-Fri 09:00-15:30)."""
    now_wib = datetime.now(WIB)
    if now_wib.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    market_open = now_wib.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now_wib.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now_wib <= market_close


def run_fetch_cycle(force: bool = False):
    """Main scheduler job: fetch all active tickers, compute technicals, store to DB.
    Pass force=True to bypass the market-hours check (used on startup)."""
    if not force and not is_market_open():
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
                db.upsert_stock(conn, ticker=ticker, name=data["name"], sector=data["sector"])
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
            time.sleep(2)

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
    """Weekly job: re-scrape IDX membership and update stocks table. Also prunes ihsg_history."""
    conn = db.get_connection()
    try:
        seed_stocks_table(conn, use_scrape=True)
        db.prune_ihsg_history(conn)
    except Exception as e:
        logger.error("Weekly refresh failed: %s", e)
    finally:
        conn.close()


def _cold_start_fetch():
    """Run fetch cycle for ALL tickers ignoring market hours — for cold start with empty DB."""
    conn = db.get_connection()
    try:
        tickers = [s["ticker"] for s in db.get_all_active_stocks(conn)]
        logger.info("Cold start fetch for %d tickers", len(tickers))
        for ticker in tickers:
            try:
                data = fetch_stock_snapshot(ticker)
                indicators = compute_technicals(data["closes"])
                db.upsert_stock(conn, ticker=ticker, name=data["name"], sector=data["sector"])
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
            time.sleep(2)
        # Also fetch IHSG so the Dashboard has data from first boot
        try:
            ihsg = fetch_ihsg()
            for bar in ihsg["bars"]:
                db.append_ihsg_history(conn, datetime=bar["datetime"], close=bar["close"])
        except Exception as e:
            logger.error("Cold start IHSG fetch failed: %s", e)
    finally:
        conn.close()


def setup_scheduler(app):
    """
    Initialize scheduler and attach to FastAPI app lifecycle.
    - Creates DB schema if needed
    - Seeds stocks table on first run (empty DB)
    - Triggers immediate fetch on cold start or if market is currently open
    - Schedules 5-min fetch job (market hours only) and weekly refresh
    Returns the scheduler instance.
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
        logger.info("Cold start: triggering immediate fetch for all tickers")
        _cold_start_fetch()
    elif not has_snapshots:
        logger.info("Tickers seeded but no snapshots yet — triggering cold start fetch")
        _cold_start_fetch()
    else:
        logger.info("Startup fetch — refreshing latest data (market %s)", "open" if is_market_open() else "closed")
        run_fetch_cycle(force=True)

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
