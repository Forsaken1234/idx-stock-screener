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
    all_tickers = get_all_tickers(use_scrape=False)
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
