"""Daily signal runner — generates trade signals for the full universe."""

import os
from datetime import datetime

import pandas as pd

from universe import UNIVERSE, get_tickers
from signals import generate_signals
from position_sizing import size_position

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ACCOUNT_EQUITY = 50_000  # GBP — update as needed


def load_data(ticker):
    """Load parquet for a ticker."""
    safe_name = ticker.replace(".", "_")
    path = os.path.join(DATA_DIR, f"{safe_name}.parquet")
    if not os.path.exists(path):
        return None
    return pd.read_parquet(path)


def run_signals(account_equity=ACCOUNT_EQUITY):
    """Run signal generation and position sizing for all instruments."""
    results = []

    for instrument in UNIVERSE:
        ticker = instrument["ticker"]
        df = load_data(ticker)
        if df is None:
            continue

        sig = generate_signals(df)
        latest = sig.iloc[-1]

        # Only size if signal is long
        pos = None
        if latest["signal"] == 1:
            pos = size_position(latest["close"], latest["atr"], account_equity)

        results.append({
            "ticker": ticker,
            "name": instrument["name"],
            "asset_class": instrument["asset_class"],
            "close": round(latest["close"], 4),
            "signal": int(latest["signal"]),
            "ema_fast": round(latest["ema_fast"], 4),
            "ema_slow": round(latest["ema_slow"], 4),
            "atr": round(latest["atr"], 4),
            "trending": bool(latest["trending"]),
            "shares": pos["shares"] if pos else 0,
            "position_value": pos["position_value"] if pos else 0,
            "stop_price": pos["stop_price"] if pos else 0,
        })

    return pd.DataFrame(results)


def main():
    print(f"Signal run: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Account equity: £{ACCOUNT_EQUITY:,.0f}\n")

    df = run_signals()

    # Show all signals
    longs = df[df["signal"] == 1]
    flats = df[df["signal"] == 0]

    if not longs.empty:
        print(f"🟢 LONG SIGNALS ({len(longs)}):")
        print(longs[["ticker", "name", "close", "atr", "shares", "position_value", "stop_price"]].to_string(index=False))
    else:
        print("No long signals today.")

    print(f"\n⚪ FLAT ({len(flats)}): {', '.join(flats['ticker'].tolist())}")
    print(f"\nTotal exposure if all filled: £{longs['position_value'].sum():,.0f}")


if __name__ == "__main__":
    main()
