"""IBKR connection via ib_insync. Connects to TWS or IB Gateway."""

from ib_insync import IB, Stock, Contract

# Paper trading defaults (TWS paper = 7497, Gateway paper = 4002)
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7497
DEFAULT_CLIENT_ID = 1


def connect(host=DEFAULT_HOST, port=DEFAULT_PORT, client_id=DEFAULT_CLIENT_ID):
    """Connect to TWS/Gateway. Returns IB instance."""
    ib = IB()
    ib.connect(host, port, clientId=client_id)
    print(f"✅ Connected to IBKR | Account: {ib.managedAccounts()} | Paper: port {port}")
    return ib


def make_contract(ticker, instrument_meta):
    """Create an IB contract from our universe metadata."""
    exchange = instrument_meta["exchange"]
    currency = instrument_meta["currency"]

    # Strip .L suffix for IBKR — LSE tickers use SMART routing
    symbol = ticker.replace(".L", "")

    if exchange == "LSE":
        return Stock(symbol, "SMART", currency, primaryExchange="LSE")
    else:
        return Stock(symbol, "SMART", currency)


def get_positions(ib):
    """Get current positions as dict {symbol: quantity}."""
    positions = {}
    for pos in ib.positions():
        sym = pos.contract.symbol
        positions[sym] = pos.position
    return positions


def get_account_equity(ib):
    """Get net liquidation value (account equity) in base currency."""
    ib.reqAccountSummary()
    for item in ib.accountSummary():
        if item.tag == "NetLiquidation" and item.currency == "BASE":
            return float(item.value)
    return None
