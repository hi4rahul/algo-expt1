"""Order execution — place market-on-open orders via IBKR, log to CGT."""

from datetime import datetime
from ib_insync import MarketOrder

from cgt_log import log_trade


def place_buy(ib, contract, quantity, instrument_meta, gbp_rate=1.0):
    """Place a market order to buy at next open. Logs to CGT."""
    order = MarketOrder("BUY", quantity)
    order.tif = "OPG"  # At the open

    trade = ib.placeOrder(contract, order)
    print(f"  📤 BUY {quantity} {contract.symbol} (OPG order placed)")

    # Log immediately — fill price updated later
    log_trade({
        "ticker": instrument_meta["ticker"],
        "name": instrument_meta["name"],
        "action": "BUY",
        "quantity": quantity,
        "price": 0,  # updated on fill
        "currency": instrument_meta["currency"],
        "gbp_rate": gbp_rate,
        "gross_gbp": 0,
        "fees_gbp": 0,
        "net_gbp": 0,
        "notes": "OPG order placed, awaiting fill",
    })
    return trade


def place_sell(ib, contract, quantity, instrument_meta, entry_date, entry_price, gbp_rate=1.0):
    """Place a market order to sell at next open. Logs to CGT with P&L."""
    order = MarketOrder("SELL", quantity)
    order.tif = "OPG"

    trade = ib.placeOrder(contract, order)
    print(f"  📤 SELL {quantity} {contract.symbol} (OPG order placed)")

    holding_days = (datetime.now() - datetime.strptime(entry_date, "%Y-%m-%d")).days

    log_trade({
        "ticker": instrument_meta["ticker"],
        "name": instrument_meta["name"],
        "action": "SELL",
        "quantity": quantity,
        "price": 0,  # updated on fill
        "currency": instrument_meta["currency"],
        "gbp_rate": gbp_rate,
        "gross_gbp": 0,
        "fees_gbp": 0,
        "net_gbp": 0,
        "entry_date": entry_date,
        "entry_price": entry_price,
        "pnl_gbp": 0,  # updated on fill
        "holding_days": holding_days,
        "notes": "OPG order placed, awaiting fill",
    })
    return trade
