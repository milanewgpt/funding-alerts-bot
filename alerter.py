import time
import httpx
import logging
from signal_engine import Signal
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

log = logging.getLogger(__name__)

TG_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"


def _fmt_liq(usd: float) -> str:
    if usd >= 1_000_000:
        return f"${usd/1_000_000:.1f}M"
    if usd >= 1_000:
        return f"${usd/1_000:.0f}k"
    return f"${usd:.0f}"


def _fmt_funding_count(next_funding_time_ms: int) -> str:
    if not next_funding_time_ms:
        return "—"
    minutes_left = max(0, (next_funding_time_ms / 1000 - time.time()) / 60)
    # guess interval from minutes_left
    if minutes_left <= 65:
        interval = "1h"
    elif minutes_left <= 260:
        interval = "4h"
    else:
        interval = "8h"
    return f"{int(minutes_left)}m ({interval})"


def _chart_url(sig: Signal) -> str:
    if sig.exchange == "BingX":
        base = sig.symbol.replace("-USDT", "")
        return f"https://www.tradingview.com/chart/?symbol=BINGX:{base}-USDT"
    base = sig.symbol.replace("USDT", "")
    return f"https://www.tradingview.com/chart/?symbol=BINANCE:{base}USDT.P"


def format_message(sig: Signal) -> str:
    emoji = "🔥 Strong signal" if sig.strong else "🟢 Long setup"
    liq_line = f"\n🔥 Short liquidations: {_fmt_liq(sig.short_liq)}" if sig.strong else ""
    funding_count = _fmt_funding_count(sig.next_funding_time)
    chart = _chart_url(sig)

    return (
        f"{emoji} — {sig.symbol} ({sig.exchange})\n"
        f"\n⚙️ Funding 30m: {sig.funding_prev:+.2f}% → {sig.funding_now:+.2f}%"
        f"\n⌛️ Funding count: {funding_count}"
        f"\n💰 Price: {sig.price_prev} → {sig.price_now} ({sig.price_change_pct:+.4f}%)"
        f"\n📈 OI: {sig.oi_change_pct:+.1f}%"
        f"{liq_line}"
        f"\n\n📊 Chart: {chart}"
    )


def send_signal(sig: Signal):
    text = format_message(sig)
    try:
        resp = httpx.post(TG_URL, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=10)
        resp.raise_for_status()
        log.info(f"Alert sent: {sig.symbol}")
    except Exception as e:
        log.error(f"Failed to send alert for {sig.symbol}: {e}")


def send_signals(signals: list[Signal]):
    for sig in signals:
        send_signal(sig)
