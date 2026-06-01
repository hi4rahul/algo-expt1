"""Alpaca order execution — market orders with CGT logging (alpaca-py SDK)."""

from datetime import datetime
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from cgt_log import log_trade


def place_buy(client, ticker, quantity, instrument_meta, gbp_rate=1.0):
    """Place market buy via Alpaca. Logs to CGT."""
    req = MarketOrderRequest(
        symbol=ticker,
        qty=quantity,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.OPG,
    )
    order = client.submit_order(req)
    print(f"  📤 BUY {quantity} {ticker} (order {order.id[:8]}...)")

    log_trade({
        "ticker": ticker,
        "name": instrument_meta["name"],
        "action": "BUY",
        "quantity": quantity,
        "price": 0,
        "currency": "USD",
        "gbp_rate": gbp_rate,
        "notes": f"Alpaca order {order.id}",
    })
    return order


def place_sell(client, ticker, quantity, instrument_meta, entry_date, entry_price, gbp_rate=1.0):
    """Place market sell via Alpaca. Logs to CGT with P&L."""
    req = MarketOrderRequest(
        symbol=ticker,
        qty=quantity,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.OPG,
    )
    order = client.submit_order(req)
    print(f"  📤 SELL {quantity} {ticker} (order {order.id[:8]}...)")

    holding_days = (datetime.now() - datetime.strptime(entry_date, "%Y-%m-%d")).days if entry_date else 0

    log_trade({
        "ticker": ticker,
        "name": instrument_meta["name"],
        "action": "SELL",
        "quantity": quantity,
        "price": 0,
        "currency": "USD",
        "gbp_rate": gbp_rate,
        "entry_date": entry_date,
        "entry_price": entry_price,
        "pnl_gbp": 0,
        "holding_days": holding_days,
        "notes": f"Alpaca order {order.id}",
    })
    return order
