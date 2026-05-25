import time

# In-memory snapshot store
# Each entry: (ts: int, snap_map: dict[(symbol, exchange) -> record])
_snapshots: list[tuple[int, dict]] = []


def init_db():
    pass  # no-op for in-memory storage


def save_snapshots(records: list[dict]) -> int:
    ts = int(time.time())
    snap_map = {(r["symbol"], r["exchange"]): r for r in records}
    _snapshots.append((ts, snap_map))
    return ts


def get_snapshots_before(ts: int, lookback_seconds: int) -> list[dict]:
    target = ts - lookback_seconds
    # Per symbol: find the latest snapshot at or before target
    best: dict[tuple, tuple[int, dict]] = {}
    for snap_ts, snap_map in _snapshots:
        if snap_ts <= target:
            for key, rec in snap_map.items():
                if key not in best or snap_ts > best[key][0]:
                    best[key] = (snap_ts, rec)
    return [rec for _, rec in best.values()]


def purge_old(older_than_seconds: int = 7200):
    global _snapshots
    cutoff = int(time.time()) - older_than_seconds
    _snapshots = [(ts, m) for ts, m in _snapshots if ts >= cutoff]
