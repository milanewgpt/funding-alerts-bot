import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Signal thresholds
FUNDING_THRESHOLD = float(os.environ.get("FUNDING_THRESHOLD", "-0.10"))   # funding_now <= X%
FUNDING_DELTA_MIN = float(os.environ.get("FUNDING_DELTA_MIN", "-0.07"))   # drop over 30m <= X%
PRICE_CHANGE_MIN = float(os.environ.get("PRICE_CHANGE_MIN", "1.0"))        # %
PRICE_CHANGE_MAX = float(os.environ.get("PRICE_CHANGE_MAX", "15.0"))       # % cap — skip already-pumped coins
OI_CHANGE_MIN = float(os.environ.get("OI_CHANGE_MIN", "0.0"))             # % OI change required (0 = non-negative)
VOLUME_24H_MIN = float(os.environ.get("VOLUME_24H_MIN", "500000"))         # USD 24h volume — skip illiquid coins
SHORT_LIQ_MIN = float(os.environ.get("SHORT_LIQ_MIN", "200000"))           # USD
COOLDOWN_MINUTES = int(os.environ.get("COOLDOWN_MINUTES", "60"))           # min between same-coin alerts

# Monitoring
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "300"))   # seconds
LOOKBACK_MINUTES = int(os.environ.get("LOOKBACK_MINUTES", "30"))

DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "snapshots.db")

