import httpx
import logging
from signal_engine import Signal
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

log = logging.getLogger(__name__)

TG_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

CHART_URL = "https://www.tradingview.com/chart/?symbol=BINANCE:{symbol}USDT.P"


def _fmt_liq(usd: float) -> str:
    if usd >= 1_000_000:
        return f"${usd/1_000_000:.1f}M"
    if usd >= 1_000:
        return f"${usd/1_000:.0f}k"
    return f"${usd:.0f}"


def format_message(sig: Signal) -> str:
    emoji = "🔥 Strong signal" if sig.strong else "🟢 Long setup"
    liq_line = f"\n🔥 Short liquidations:\n{_fmt_liq(sig.short_liq)}" if sig.strong else ""
    chart = CHART_URL.format(symbol=sig.symbol.replace("USDT", ""))

    return (
        f"{emoji} — {sig.symbol}\n"
        f"\n⚙️ Funding:\n"
        f"{sig.funding_prev:+.4f}% → {sig.funding_now:+.4f}%"
        f"\n\n💰 Price:\n"
        f"{sig.price_prev:.4f} → {sig.price_now:.4f}\n"
        f"{sig.price_change_pct:+.2f}%"
        f"\n\n📈 OI:\n"
        f"{sig.oi_change_pct:+.1f}%"
        f"{liq_line}"
        f"\n\n📊 Chart:\n{chart}"
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
