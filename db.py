import sqlite3
import time
from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            exchange TEXT NOT NULL,
            funding_rate REAL,
            price REAL,
            oi REAL,
            short_liq REAL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ts_symbol ON snapshots(ts, symbol)")
    conn.commit()
    conn.close()


def save_snapshots(records: list[dict]):
    ts = int(time.time())
    conn = sqlite3.connect(DB_PATH)
    conn.executemany(
        "INSERT INTO snapshots(ts, symbol, exchange, funding_rate, price, oi, short_liq) "
        "VALUES (:ts, :symbol, :exchange, :funding_rate, :price, :oi, :short_liq)",
        [{**r, "ts": ts} for r in records],
    )
    conn.commit()
    conn.close()
    return ts


def get_snapshots_before(ts: int, lookback_seconds: int) -> list[dict]:
    target = ts - lookback_seconds
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Get snapshot closest to (ts - lookback), per symbol
    rows = conn.execute("""
        SELECT s.*
        FROM snapshots s
        INNER JOIN (
            SELECT symbol, MAX(ts) AS max_ts
            FROM snapshots
            WHERE ts <= :target
            GROUP BY symbol
        ) best ON s.symbol = best.symbol AND s.ts = best.max_ts
    """, {"target": target}).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def purge_old(older_than_seconds: int = 7200):
    cutoff = int(time.time()) - older_than_seconds
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM snapshots WHERE ts < ?", (cutoff,))
    conn.commit()
    conn.close()
