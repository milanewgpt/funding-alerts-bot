import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Signal thresholds
FUNDING_THRESHOLD = float(os.environ.get("FUNDING_THRESHOLD", "-0.05"))   # %
PRICE_CHANGE_MIN = float(os.environ.get("PRICE_CHANGE_MIN", "1.0"))        # %
OI_CHANGE_MIN = float(os.environ.get("OI_CHANGE_MIN", "5.0"))              # %
SHORT_LIQ_MIN = float(os.environ.get("SHORT_LIQ_MIN", "200000"))           # USD

# Monitoring
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "300"))   # seconds
LOOKBACK_MINUTES = int(os.environ.get("LOOKBACK_MINUTES", "30"))

# Top N coins by OI to monitor
TOP_N_COINS = int(os.environ.get("TOP_N_COINS", "100"))

DATA_DIR = os.environ.get("DATA_DIR", "/home/gpt/funding-alerts-bot/data")
DB_PATH = os.path.join(DATA_DIR, "snapshots.db")
