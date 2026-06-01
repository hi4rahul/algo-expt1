"""Daily trading script for Alpaca — US stocks only.

Usage:
  python3 trade_alpaca.py          # dry run
  python3 trade_alpaca.py --live   # place real orders on Alpaca paper
"""

import sys
from datetime import datetime

import pandas as pd

from universe import get_by_asset_class
from signals import generate_signals
from position_sizing import size_position
from alpaca_connection import connect, get_positions, get_account_equity
from alpaca_execution import place_buy, place_sell
from cgt_log import read_open_positions

import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEFAULT_EQUITY = 50_000  # USD for Alpaca


def load_data(ticker):
    safe_name = ticker.replace(".", "_")
    path = os.path.join(DATA_DIR, f"{safe_name}.parquet")
    if not os.path.exists(path):
        return None
    return pd.read_parquet(path)


def run(live=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    us_stocks = get_by_asset_class("us_stock")

    print(f"{'🔴 LIVE' if live else '⚪ DRY RUN'} | Alpaca (US stocks) | {timestamp}")
    print("=" * 60)

    api = None
    equity = DEFAULT_EQUITY
    current_positions = {}

    if live:
        api = connect()
        equity = get_account_equity(api)
        current_positions = get_positions(api)
        print(f"Positions: {current_positions or 'none'}")
    else:
        print(f"Account equity (assumed): ${equity:,.0f}")

    cgt_positions = read_open_positions()

    buys = []
    sells = []

    for instrument in us_stocks:
        ticker = instrument["ticker"]
        df = load_data(ticker)
        if df is None:
            continue

        sig = generate_signals(df)
        latest = sig.iloc[-1]
        signal = int(latest["signal"])
        close = latest["close"]
        atr = latest["atr"]

        held = ticker in current_positions and current_positions[ticker] > 0
        has_cgt_entry = ticker in cgt_positions and len(cgt_positions[ticker]) > 0

        if signal == 1 and not held:
            pos = size_position(close, atr, equity)
            if pos:
                buys.append({"instrument": instrument, "shares": pos["shares"], "close": close, "pos": pos})

        elif signal == 0 and (held or has_cgt_entry):
            qty = current_positions.get(ticker, 0)
            entry_info = cgt_positions.get(ticker, [{}])[0]
            sells.append({
                "instrument": instrument,
                "shares": qty if qty > 0 else int(entry_info.get("quantity", 0)),
                "entry_date": entry_info.get("date", ""),
                "entry_price": entry_info.get("price", "0"),
            })

    print(f"\n🟢 BUY ORDERS ({len(buys)}):")
    for b in buys:
        print(f"  {b['instrument']['ticker']:<8} {b['shares']:>5} shares @ ~${b['close']:.2f}  (value: ${b['pos']['position_value']:,.0f}, stop: ${b['pos']['stop_price']:.2f})")

    print(f"\n🔴 SELL ORDERS ({len(sells)}):")
    for s in sells:
        print(f"  {s['instrument']['ticker']:<8} {s['shares']:>5} shares  (entry: {s['entry_date']})")

    if not buys and not sells:
        print("\n  No trades today.")

    if live and (buys or sells):
        print(f"\n{'=' * 60}")
        print("EXECUTING ORDERS...")
        for b in buys:
            place_buy(api, b["instrument"]["ticker"], b["shares"], b["instrument"])
        for s in sells:
            if s["shares"] > 0:
                place_sell(api, s["instrument"]["ticker"], s["shares"], s["instrument"], s["entry_date"], s["entry_price"])
        print("\n✅ All orders placed (OPG — will fill at next open)")

    print(f"\n{'=' * 60}")
    total_buy = sum(b["pos"]["position_value"] for b in buys)
    print(f"Summary: {len(buys)} buys (${total_buy:,.0f}), {len(sells)} sells")


if __name__ == "__main__":
    live = "--live" in sys.argv
    run(live=live)
