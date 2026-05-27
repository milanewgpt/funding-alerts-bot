import logging
from dataclasses import dataclass
from config import FUNDING_THRESHOLD, PRICE_CHANGE_MIN, PRICE_CHANGE_MAX, OI_CHANGE_MIN, VOLUME_24H_MIN, SHORT_LIQ_MIN

log = logging.getLogger(__name__)


@dataclass
class Signal:
    symbol: str
    exchange: str
    funding_prev: float
    funding_now: float
    funding_delta: float       # funding_now - funding_prev
    price_prev: float
    price_now: float
    price_change_pct: float
    oi_change_pct: float
    short_liq: float
    next_funding_time: int     # ms timestamp
    strong: bool


def evaluate(current: list[dict], previous: list[dict]) -> list[Signal]:
    prev_map = {(r["symbol"], r["exchange"]): r for r in previous}
    signals = []

    for rec in current:
        symbol = rec["symbol"]
        exchange = rec["exchange"]
        prev = prev_map.get((symbol, exchange))
        if not prev:
            continue

        funding_now = rec.get("funding_rate")
        price_now = rec.get("price")
        oi_now = rec.get("oi")
        short_liq = rec.get("short_liq", 0) or 0
        next_ft = rec.get("next_funding_time", 0) or 0

        funding_prev = prev.get("funding_rate")
        price_prev = prev.get("price")
        oi_prev = prev.get("oi")

        if any(v is None for v in [funding_now, price_now, funding_prev, price_prev]):
            continue
        if price_prev == 0:
            continue

        # Filter 1: 30m ago funding was at/above threshold (fresh crossing only)
        if funding_prev < FUNDING_THRESHOLD:
            continue

        # Filter 2: now funding is at/below threshold
        if funding_now > FUNDING_THRESHOLD:
            continue

        funding_delta = funding_now - funding_prev

        # Filter 3: funding must be getting more negative (not static)
        if funding_delta >= 0:
            continue

        # Filter 4: price must be rising but not already pumped
        price_change = (price_now - price_prev) / price_prev * 100
        if price_change < PRICE_CHANGE_MIN:
            continue
        if price_change > PRICE_CHANGE_MAX:
            continue

        volume_24h = rec.get("volume_24h", 0) or 0

        # Filter 5: minimum liquidity (24h volume)
        if volume_24h < VOLUME_24H_MIN:
            continue

        oi_change = 0.0
        if oi_prev and oi_prev != 0 and oi_now:
            oi_change = (oi_now - oi_prev) / oi_prev * 100

        # Filter 5: OI must be growing (not contracting)
        if oi_change < OI_CHANGE_MIN:
            continue

        strong = short_liq >= SHORT_LIQ_MIN

        signals.append(Signal(
            symbol=symbol,
            exchange=exchange,
            funding_prev=funding_prev,
            funding_now=funding_now,
            funding_delta=funding_delta,
            price_prev=price_prev,
            price_now=price_now,
            price_change_pct=price_change,
            oi_change_pct=oi_change,
            short_liq=short_liq,
            next_funding_time=next_ft,
            strong=strong,
        ))
        log.info(
            f"Signal: [{exchange}] {symbol} funding={funding_now:+.4f}% "
            f"(Δ{funding_delta:+.4f}%) price={price_change:+.2f}%"
        )

    return signals
