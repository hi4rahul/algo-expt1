"""Universe definition — all tradeable instruments with metadata."""

UNIVERSE = [
    # Irish-domiciled ETFs on LSE (stamp duty free)
    {"ticker": "CSPX.L", "name": "iShares Core S&P 500", "asset_class": "equity_etf", "exchange": "LSE", "currency": "USD"},
    {"ticker": "CNDX.L", "name": "iShares Nasdaq 100", "asset_class": "equity_etf", "exchange": "LSE", "currency": "USD"},
    {"ticker": "ISF.L", "name": "iShares FTSE 100", "asset_class": "equity_etf", "exchange": "LSE", "currency": "GBP"},
    {"ticker": "VWRL.L", "name": "Vanguard FTSE All-World", "asset_class": "equity_etf", "exchange": "LSE", "currency": "USD"},
    {"ticker": "IWDA.L", "name": "iShares MSCI World", "asset_class": "equity_etf", "exchange": "LSE", "currency": "USD"},
    {"ticker": "EMIM.L", "name": "iShares MSCI Emerging Markets", "asset_class": "equity_etf", "exchange": "LSE", "currency": "USD"},
    {"ticker": "IMEU.L", "name": "iShares Core MSCI Europe", "asset_class": "equity_etf", "exchange": "LSE", "currency": "EUR"},
    {"ticker": "IGLN.L", "name": "iShares Physical Gold", "asset_class": "commodity_etf", "exchange": "LSE", "currency": "USD"},
    # Crypto ETNs on LSE (stamp duty free)
    {"ticker": "BTCE.L", "name": "WisdomTree Bitcoin", "asset_class": "crypto_etn", "exchange": "LSE", "currency": "USD"},
    {"ticker": "ETHW.L", "name": "WisdomTree Ethereum", "asset_class": "crypto_etn", "exchange": "LSE", "currency": "USD"},
    {"ticker": "SOLW.L", "name": "WisdomTree Solana", "asset_class": "crypto_etn", "exchange": "LSE", "currency": "USD"},
    {"ticker": "BLOC.L", "name": "WisdomTree Crypto Market", "asset_class": "crypto_etn", "exchange": "LSE", "currency": "USD"},
    # US large cap stocks (no UK stamp duty)
    {"ticker": "AAPL", "name": "Apple", "asset_class": "us_stock", "exchange": "NASDAQ", "currency": "USD"},
    {"ticker": "MSFT", "name": "Microsoft", "asset_class": "us_stock", "exchange": "NASDAQ", "currency": "USD"},
    {"ticker": "NVDA", "name": "NVIDIA", "asset_class": "us_stock", "exchange": "NASDAQ", "currency": "USD"},
    {"ticker": "AMZN", "name": "Amazon", "asset_class": "us_stock", "exchange": "NASDAQ", "currency": "USD"},
    {"ticker": "META", "name": "Meta Platforms", "asset_class": "us_stock", "exchange": "NASDAQ", "currency": "USD"},
    {"ticker": "GOOGL", "name": "Alphabet", "asset_class": "us_stock", "exchange": "NASDAQ", "currency": "USD"},
    {"ticker": "TSLA", "name": "Tesla", "asset_class": "us_stock", "exchange": "NASDAQ", "currency": "USD"},
    {"ticker": "JPM", "name": "JPMorgan Chase", "asset_class": "us_stock", "exchange": "NYSE", "currency": "USD"},
    {"ticker": "V", "name": "Visa", "asset_class": "us_stock", "exchange": "NYSE", "currency": "USD"},
    {"ticker": "UNH", "name": "UnitedHealth", "asset_class": "us_stock", "exchange": "NYSE", "currency": "USD"},
]


def get_tickers():
    """Return list of all tickers."""
    return [i["ticker"] for i in UNIVERSE]


def get_by_asset_class(asset_class):
    """Filter universe by asset class."""
    return [i for i in UNIVERSE if i["asset_class"] == asset_class]
