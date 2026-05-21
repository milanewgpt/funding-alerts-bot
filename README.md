# Funding Alerts Bot

Funding-rate and market-structure alert bot for crypto futures monitoring.

The bot periodically collects market snapshots, compares current data with historical data, evaluates funding/price/open-interest/liquidation conditions, and sends Telegram alerts when configured thresholds are met.

## Features

- Periodic market snapshot collection.
- SQLite storage for recent data.
- Funding-rate threshold detection.
- Price, open-interest, and liquidation filters.
- Telegram alert delivery.
- systemd service file for VPS deployment.

## Environment

```bash
cp .env.example .env
```

Required variables:

- `TELEGRAM_TOKEN` — Telegram bot token.
- `TELEGRAM_CHAT_ID` — target Telegram chat ID.

Optional variables:

- `FUNDING_THRESHOLD` — current funding threshold.
- `FUNDING_DELTA_MIN` — minimum funding drop over the lookback window.
- `PRICE_CHANGE_MIN` — minimum price change percentage.
- `OI_CHANGE_MIN` — minimum open-interest change percentage.
- `SHORT_LIQ_MIN` — minimum short liquidation amount in USD.
- `POLL_INTERVAL` — polling interval in seconds.
- `LOOKBACK_MINUTES` — lookback window.
- `TOP_N_COINS` — number of coins to monitor.
- `DATA_DIR` — data directory for the SQLite database.

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python main.py
```

## Deploy as systemd

```bash
sudo cp systemd/funding-alerts.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable funding-alerts
sudo systemctl start funding-alerts
sudo journalctl -u funding-alerts -f
```

## Risk Notes

- Alerts are signals, not trade instructions.
- Funding spikes can reverse quickly.
- Use alerts as a filter for further review, not as automated execution logic.

## Security

- Do not commit `.env`.
- Store Telegram credentials only in environment variables.
