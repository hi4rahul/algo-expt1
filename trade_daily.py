"""Daily trading script — run after market close to place orders for next open.

Usage:
  python3 trade_daily.py          # dry run (no orders)
  python3 trade_daily.py --live   # place real orders on paper account
"""

import sys
import os
from datetime import datetime

import pandas as pd

from universe import UNIVERSE
from signals import generate_signals
from position_sizing import size_position
from ibkr_connection import connect, make_contract, get_positions, get_account_equity
from order_execution import place_buy, place_sell
from cgt_log import read_open_positions

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEFAULT_EQUITY = 50_000


def load_data(ticker):
    safe_name = ticker.replace(".", "_")
    path = os.path.join(DATA_DIR, f"{safe_name}.parquet")
    if not os.path.exists(path):
        return None
    return pd.read_parquet(path)


def compute_signals():
    """Generate signals for all instruments. Returns list of dicts."""
    results = []
    for instrument in UNIVERSE:
        ticker = instrument["ticker"]
        df = load_data(ticker)
        if df is None:
            continue
        sig = generate_signals(df)
        latest = sig.iloc[-1]
        results.append({
            "instrument": instrument,
            "signal": int(latest["signal"]),
            "close": latest["close"],
            "atr": latest["atr"],
        })
    return results


def run(live=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"{'🔴 LIVE' if live else '⚪ DRY RUN'} | {timestamp}")
    print("=" * 60)

    # Connect to IBKR if live
    ib = None
    equity = DEFAULT_EQUITY
    current_positions = {}

    if live:
        ib = connect()
        equity = get_account_equity(ib) or DEFAULT_EQUITY
        current_positions = get_positions(ib)
        print(f"Account equity: £{equity:,.0f}")
        print(f"Current positions: {current_positions or 'none'}")
    else:
        print(f"Account equity (assumed): £{equity:,.0f}")

    # Get open positions from CGT log (for exit matching)
    cgt_positions = read_open_positions()

    # Generate signals
    signals = compute_signals()
    buys = []
    sells = []

    for item in signals:
        instrument = item["instrument"]
        ticker = instrument["ticker"]
        symbol = ticker.replace(".L", "")
        signal = item["signal"]
        close = item["close"]
        atr = item["atr"]

        held = symbol in current_positions and current_positions[symbol] > 0
        has_cgt_entry = ticker in cgt_positions and len(cgt_positions[ticker]) > 0

        if signal == 1 and not held:
            # New long signal, not already in position
            pos = size_position(close, atr, equity)
            if pos:
                buys.append({"instrument": instrument, "shares": pos["shares"], "close": close, "pos": pos})

        elif signal == 0 and (held or has_cgt_entry):
            # Exit signal, currently holding
            qty = int(current_positions.get(symbol, 0))
            entry_info = cgt_positions.get(ticker, [{}])[0]
            sells.append({
                "instrument": instrument,
                "shares": qty if qty > 0 else int(entry_info.get("quantity", 0)),
                "entry_date": entry_info.get("date", ""),
                "entry_price": entry_info.get("price", "0"),
            })

    # Print summary
    print(f"\n🟢 BUY ORDERS ({len(buys)}):")
    for b in buys:
        print(f"  {b['instrument']['ticker']:<10} {b['shares']:>5} shares @ ~{b['close']:.2f}  (value: £{b['pos']['position_value']:,.0f}, stop: {b['pos']['stop_price']:.2f})")

    print(f"\n🔴 SELL ORDERS ({len(sells)}):")
    for s in sells:
        print(f"  {s['instrument']['ticker']:<10} {s['shares']:>5} shares  (entry: {s['entry_date']})")

    if not buys and not sells:
        print("\n  No trades today.")

    # Execute if live
    if live and (buys or sells):
        print(f"\n{'=' * 60}")
        print("EXECUTING ORDERS...")

        for b in buys:
            contract = make_contract(b["instrument"]["ticker"], b["instrument"])
            place_buy(ib, contract, b["shares"], b["instrument"])

        for s in sells:
            if s["shares"] > 0:
                contract = make_contract(s["instrument"]["ticker"], s["instrument"])
                place_sell(ib, contract, s["shares"], s["instrument"], s["entry_date"], s["entry_price"])

        print("\n✅ All orders placed (OPG — will fill at next open)")

    if ib:
        ib.disconnect()

    print(f"\n{'=' * 60}")
    total_buy = sum(b["pos"]["position_value"] for b in buys)
    print(f"Summary: {len(buys)} buys (£{total_buy:,.0f}), {len(sells)} sells")


if __name__ == "__main__":
    live = "--live" in sys.argv
    run(live=live)
