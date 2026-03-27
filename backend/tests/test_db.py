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
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
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
    # Insert 3 bars in chronological order
    append_price_history(conn, ticker="BBCA", datetime="2026-03-27T09:00:00",
                         open=9100, high=9250, low=9080, close=9200, volume=4200000)
    append_price_history(conn, ticker="BBCA", datetime="2026-03-27T09:05:00",
                         open=9200, high=9300, low=9190, close=9250, volume=3800000)
    append_price_history(conn, ticker="BBCA", datetime="2026-03-27T09:10:00",
                         open=9250, high=9350, low=9240, close=9300, volume=4100000)
    history = get_price_history(conn, "BBCA")
    assert len(history) == 3
    # Result should be sorted ascending (oldest first for chart display)
    assert history[0]["datetime"] == "2026-03-27T09:00:00"
    assert history[-1]["datetime"] == "2026-03-27T09:10:00"
    assert history[-1]["close"] == 9300

def test_price_history_limit_returns_most_recent(conn):
    from db import upsert_stock, append_price_history, get_price_history
    upsert_stock(conn, ticker="BBCA", name="Bank Central Asia", sector="Finance")
    for i in range(5):
        append_price_history(conn, ticker="BBCA", datetime=f"2026-03-27T09:0{i}:00",
                             open=9100+i*10, high=9200+i*10, low=9090+i*10,
                             close=9150+i*10, volume=1000000)
    # limit=3 should return the 3 most recent, sorted ascending
    history = get_price_history(conn, "BBCA", limit=3)
    assert len(history) == 3
    assert history[0]["datetime"] == "2026-03-27T09:02:00"  # 3rd oldest = 1st of most recent 3
    assert history[-1]["datetime"] == "2026-03-27T09:04:00"  # most recent

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
