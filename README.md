# Algo Trading System

Multi-asset trend following for IBKR UK (GIA account). Daily signals, no leverage, stamp duty free instruments only.

## Strategy

- EMA 8/21 crossover + ATR trend filter
- Position sizing: 1% risk per trade, 2x ATR stop, 10% max position
- Holding period: 3–20 days
- Signals generated after close, orders placed at next open (OPG)

## Usage

```bash
# Stage 1: Download data
python3 pipeline.py

# Stage 2: Check today's signals
python3 run_signals.py

# Stage 3: Run backtest
python3 backtest.py

# Stage 4: Paper trading
python3 trade_daily.py          # dry run
python3 trade_daily.py --live   # place orders (TWS must be running on port 7497)
```

## IBKR Setup

1. Open TWS Paper Trading (port 7497)
2. Enable API: Configure → API → Enable ActiveX and Socket Clients
3. Uncheck "Read-Only API"
4. Run `python3 trade_daily.py --live`

## Files

| File | Purpose |
|------|---------|
| `universe.py` | 22 instruments with metadata |
| `pipeline.py` | Data download & validation |
| `signals.py` | EMA crossover + ATR trend filter |
| `position_sizing.py` | Volatility-scaled sizing |
| `run_signals.py` | Daily signal check |
| `backtest.py` | Full backtest with vectorbt |
| `trade_daily.py` | Daily trading (dry run or live) |
| `ibkr_connection.py` | TWS API connection |
| `order_execution.py` | Order placement (OPG market orders) |
| `cgt_log.py` | CGT trade logging (CSV) |
| `cgt_trade_log.csv` | Trade history for tax reporting |

## CGT Log Fields

Every trade records: date, ticker, action, quantity, price, currency, GBP rate, fees, P&L in GBP, holding days.
