"""Alpaca connection — paper trading for US stocks (alpaca-py SDK)."""

import os
from alpaca.trading.client import TradingClient


PAPER = True


def connect():
    """Connect to Alpaca paper trading. Keys from env vars."""
    api_key = os.environ.get("ALPACA_API_KEY")
    secret_key = os.environ.get("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        raise RuntimeError(
            "Set ALPACA_API_KEY and ALPACA_SECRET_KEY env vars.\n"
            "  export ALPACA_API_KEY='...'\n"
            "  export ALPACA_SECRET_KEY='...'"
        )

    client = TradingClient(api_key, secret_key, paper=PAPER)
    account = client.get_account()
    print(f"✅ Connected to Alpaca Paper | Equity: ${float(account.equity):,.2f} | Status: {account.status}")
    return client


def get_positions(client):
    """Get current positions as dict {symbol: quantity}."""
    return {p.symbol: int(p.qty) for p in client.get_all_positions()}


def get_account_equity(client):
    """Get account equity in USD."""
    return float(client.get_account().equity)
