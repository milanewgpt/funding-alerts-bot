import logging
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import TOP_N_COINS

log = logging.getLogger(__name__)

BASE = "https://fapi.binance.com"
CLIENT = httpx.Client(timeout=15)


def _get(path: str, params: dict = None) -> list | dict:
    resp = CLIENT.get(f"{BASE}{path}", params=params)
    resp.raise_for_status()
    return resp.json()


def fetch_funding_and_prices() -> tuple[dict[str, float], dict[str, float], dict[str, int]]:
    """Returns (funding_map, price_map, next_funding_time_map) for all USDT perpetuals."""
    data = _get("/fapi/v1/premiumIndex")
    funding = {}
    prices = {}
    next_ft = {}
    for item in data:
        symbol = item["symbol"]
        if not symbol.endswith("USDT"):
            continue
        funding[symbol] = float(item["lastFundingRate"]) * 100  # convert to %
        prices[symbol] = float(item["markPrice"])
        next_ft[symbol] = int(item["nextFundingTime"])  # ms timestamp
    return funding, prices, next_ft


def fetch_top_symbols_by_volume(n: int) -> list[str]:
    """Top N symbols by 24h quote volume."""
    data = _get("/fapi/v1/ticker/24hr")
    usdt = [d for d in data if d["symbol"].endswith("USDT")]
    usdt.sort(key=lambda x: float(x["quoteVolume"]), reverse=True)
    return [d["symbol"] for d in usdt[:n]]


def _fetch_oi_one(symbol: str, price: float) -> tuple[str, float | None]:
    try:
        data = _get("/fapi/v1/openInterest", {"symbol": symbol})
        # openInterest is in base asset; multiply by price for USD value
        return symbol, float(data["openInterest"]) * price
    except Exception as e:
        log.debug(f"OI error {symbol}: {e}")
        return symbol, None


def fetch_open_interest(symbols: list[str], prices: dict[str, float]) -> dict[str, float]:
    """Returns {symbol: oi_usd} using parallel requests."""
    result = {}
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(_fetch_oi_one, s, prices.get(s, 1.0)): s for s in symbols}
        for future in as_completed(futures):
            symbol, oi = future.result()
            if oi is not None:
                result[symbol] = oi
    return result


def collect_snapshot() -> list[dict]:
    log.info("Collecting snapshot from Binance...")
    try:
        top_symbols = fetch_top_symbols_by_volume(TOP_N_COINS)
        funding, prices, next_ft = fetch_funding_and_prices()
        oi_map = fetch_open_interest(top_symbols, prices)
    except Exception as e:
        log.error(f"Binance fetch error: {e}")
        return []

    records = []
    for symbol in top_symbols:
        if symbol not in funding:
            continue
        records.append({
            "symbol": symbol,
            "exchange": "Binance",
            "funding_rate": funding.get(symbol),
            "price": prices.get(symbol),
            "oi": oi_map.get(symbol),
            "short_liq": 0.0,
            "next_funding_time": next_ft.get(symbol, 0),
        })
    log.info(f"Collected {len(records)} symbols")
    return records
