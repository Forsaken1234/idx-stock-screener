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
