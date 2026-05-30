"""CGT trade log — records all trades for UK Capital Gains Tax reporting."""

import os
import csv
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "cgt_trade_log.csv")

FIELDS = [
    "trade_id", "date", "ticker", "name", "action",  # BUY or SELL
    "quantity", "price", "currency", "gbp_rate",
    "gross_gbp", "fees_gbp", "net_gbp",
    "entry_date", "entry_price", "pnl_gbp",  # filled on SELL
    "holding_days", "notes",
]


def _ensure_log():
    """Create CSV with headers if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()


def log_trade(trade_data: dict):
    """Append a trade record to the CGT log."""
    _ensure_log()
    trade_data.setdefault("trade_id", datetime.now().strftime("%Y%m%d%H%M%S"))
    trade_data.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow({k: trade_data.get(k, "") for k in FIELDS})


def read_open_positions():
    """Read log and return open positions (BUYs without matching SELLs)."""
    _ensure_log()
    buys = {}  # ticker -> list of {date, price, quantity, ...}
    with open(LOG_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row["ticker"]
            if row["action"] == "BUY":
                buys.setdefault(ticker, []).append(row)
            elif row["action"] == "SELL":
                # Remove oldest buy (FIFO for CGT)
                if ticker in buys and buys[ticker]:
                    buys[ticker].pop(0)
    return {k: v for k, v in buys.items() if v}
