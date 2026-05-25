import logging
import time

from config import POLL_INTERVAL, LOOKBACK_MINUTES
from db import init_db, save_snapshots, get_snapshots_before, purge_old
from collector import collect_snapshot
from signal_engine import evaluate
from alerter import send_signals

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


def run_cycle():
    records = collect_snapshot()
    if not records:
        log.warning("Empty snapshot, skipping cycle")
        return

    now_ts = save_snapshots(records)
    prev_records = get_snapshots_before(now_ts, LOOKBACK_MINUTES * 60)

    if not prev_records:
        log.info("No historical data yet, accumulating...")
        return

    signals = evaluate(records, prev_records)
    if signals:
        log.info(f"Sending {len(signals)} signal(s)")
        send_signals(signals)
    else:
        log.info("No signals this cycle")

    purge_old(older_than_seconds=7200)


def main():
    init_db()
    log.info(f"Funding alerts bot started (poll={POLL_INTERVAL}s, lookback={LOOKBACK_MINUTES}m)")

    while True:
        try:
            run_cycle()
        except Exception as e:
            log.exception(f"Cycle error: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
