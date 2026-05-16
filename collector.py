import logging
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import TOP_N_COINS

log = logging.getLogger(__name__)

BINANCE_BASE = "https://fapi.binance.com"
BINGX_BASE = "https://open-api.bingx.com"
CLIENT = httpx.Client(timeout=15)


def _get(url: str, params: dict = None) -> list | dict:
    resp = CLIENT.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


# ── Binance ──────────────────────────────────────────────────────────────────

def _binance_funding_prices() -> tuple[dict, dict, dict]:
    data = _get(f"{BINANCE_BASE}/fapi/v1/premiumIndex")
    funding, prices, next_ft = {}, {}, {}
    for item in data:
        sym = item["symbol"]
        if not sym.endswith("USDT"):
            continue
        funding[sym] = float(item["lastFundingRate"]) * 100
        prices[sym] = float(item["markPrice"])
        next_ft[sym] = int(item["nextFundingTime"])
    return funding, prices, next_ft


def _binance_top_symbols(n: int) -> list[str]:
    data = _get(f"{BINANCE_BASE}/fapi/v1/ticker/24hr")
    usdt = [d for d in data if d["symbol"].endswith("USDT")]
    usdt.sort(key=lambda x: float(x["quoteVolume"]), reverse=True)
    return [d["symbol"] for d in usdt[:n]]


def _binance_oi_one(symbol: str, price: float) -> tuple[str, float | None]:
    try:
        data = _get(f"{BINANCE_BASE}/fapi/v1/openInterest", {"symbol": symbol})
        return symbol, float(data["openInterest"]) * price
    except Exception as e:
        log.debug(f"Binance OI error {symbol}: {e}")
        return symbol, None


def collect_binance(n: int) -> list[dict]:
    top = _binance_top_symbols(n)
    funding, prices, next_ft = _binance_funding_prices()
    oi_map = {}
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(_binance_oi_one, s, prices.get(s, 1.0)): s for s in top}
        for f in as_completed(futures):
            sym, oi = f.result()
            if oi is not None:
                oi_map[sym] = oi

    records = []
    for sym in top:
        if sym not in funding:
            continue
        records.append({
            "symbol": sym,
            "exchange": "Binance",
            "funding_rate": funding.get(sym),
            "price": prices.get(sym),
            "oi": oi_map.get(sym),
            "short_liq": 0.0,
            "next_funding_time": next_ft.get(sym, 0),
        })
    return records


# ── BingX ────────────────────────────────────────────────────────────────────

def _bingx_top_symbols(n: int) -> list[str]:
    data = _get(f"{BINGX_BASE}/openApi/swap/v2/quote/ticker")["data"]
    usdt = [
        d for d in data
        if d["symbol"].endswith("-USDT") and "2USD" not in d["symbol"]
    ]
    usdt.sort(key=lambda x: float(x.get("quoteVolume") or 0), reverse=True)
    return [d["symbol"] for d in usdt[:n]]


def _bingx_funding_one(symbol: str) -> tuple[str, dict | None]:
    try:
        data = _get(
            f"{BINGX_BASE}/openApi/swap/v2/quote/premiumIndex",
            {"symbol": symbol},
        )["data"]
        return symbol, data
    except Exception as e:
        log.debug(f"BingX funding error {symbol}: {e}")
        return symbol, None


def _bingx_oi_one(symbol: str, price: float) -> tuple[str, float | None]:
    try:
        data = _get(
            f"{BINGX_BASE}/openApi/swap/v2/quote/openInterest",
            {"symbol": symbol},
        )["data"]
        return symbol, float(data["openInterest"]) * price
    except Exception as e:
        log.debug(f"BingX OI error {symbol}: {e}")
        return symbol, None


def collect_bingx(n: int) -> list[dict]:
    top = _bingx_top_symbols(n)

    funding_map, prices, next_ft = {}, {}, {}
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(_bingx_funding_one, s): s for s in top}
        for f in as_completed(futures):
            sym, data = f.result()
            if data:
                funding_map[sym] = float(data["lastFundingRate"]) * 100
                prices[sym] = float(data["markPrice"])
                next_ft[sym] = int(data["nextFundingTime"])

    oi_map = {}
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(_bingx_oi_one, s, prices.get(s, 1.0)): s for s in top}
        for f in as_completed(futures):
            sym, oi = f.result()
            if oi is not None:
                oi_map[sym] = oi

    records = []
    for sym in top:
        if sym not in funding_map:
            continue
        records.append({
            "symbol": sym,
            "exchange": "BingX",
            "funding_rate": funding_map.get(sym),
            "price": prices.get(sym),
            "oi": oi_map.get(sym),
            "short_liq": 0.0,
            "next_funding_time": next_ft.get(sym, 0),
        })
    return records


# ── Combined ─────────────────────────────────────────────────────────────────

def collect_snapshot() -> list[dict]:
    log.info("Collecting snapshot from Binance + BingX...")
    records = []
    try:
        binance = collect_binance(TOP_N_COINS)
        log.info(f"Binance: {len(binance)} symbols")
        records.extend(binance)
    except Exception as e:
        log.error(f"Binance collect error: {e}")
    try:
        bingx = collect_bingx(TOP_N_COINS)
        log.info(f"BingX: {len(bingx)} symbols")
        records.extend(bingx)
    except Exception as e:
        log.error(f"BingX collect error: {e}")
    log.info(f"Total: {len(records)} records")
    return records
