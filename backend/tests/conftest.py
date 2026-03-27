import pytest
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
    from fastapi.testclient import TestClient
    return TestClient(app)
