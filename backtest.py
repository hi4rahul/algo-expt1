"""Stage 3 — Backtest trend-following strategy using vectorbt."""

import os
import numpy as np
import pandas as pd
import vectorbt as vbt

from universe import UNIVERSE
from signals import generate_signals

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INIT_EQUITY = 50_000
RISK_PCT = 0.01
ATR_MULT = 2.0
MAX_POS_PCT = 0.10


def load_data(ticker):
    safe_name = ticker.replace(".", "_")
    path = os.path.join(DATA_DIR, f"{safe_name}.parquet")
    if not os.path.exists(path):
        return None
    return pd.read_parquet(path)


def backtest_single(ticker, df):
    """Backtest one instrument. Returns vbt Portfolio."""
    sig = generate_signals(df)

    # Entry: signal goes from 0 to 1. Exit: signal goes from 1 to 0.
    entries = sig["signal"].diff() == 1
    exits = sig["signal"].diff() == -1

    # Volatility-scaled size: risk_amount / (ATR * mult) shares per entry
    atr = sig["atr"]
    close = sig["close"]
    risk_amount = INIT_EQUITY * RISK_PCT
    raw_shares = risk_amount / (atr * ATR_MULT)
    max_shares = (INIT_EQUITY * MAX_POS_PCT) / close
    size = raw_shares.clip(upper=max_shares).fillna(0).astype(int)

    pf = vbt.Portfolio.from_signals(
        close=close,
        entries=entries,
        exits=exits,
        size=size,
        size_type="amount",
        init_cash=INIT_EQUITY,
        fees=0.001,  # 10bps round-trip estimate
        freq="1D",
    )
    return pf


def run_backtest():
    """Run backtest across all instruments, return per-asset and portfolio stats."""
    results = []
    all_returns = []

    for instrument in UNIVERSE:
        ticker = instrument["ticker"]
        df = load_data(ticker)
        if df is None:
            continue

        # Need enough data for indicators to warm up
        if len(df) < 100:
            continue

        pf = backtest_single(ticker, df)
        stats = pf.stats()

        results.append({
            "ticker": ticker,
            "name": instrument["name"],
            "asset_class": instrument["asset_class"],
            "total_return_pct": round(stats.get("Total Return [%]", 0), 2),
            "cagr_pct": round((1 + stats.get("Total Return [%]", 0) / 100) ** (1 / max(stats.get("Period", 1).days / 365.25, 0.1)) - 1, 4) * 100 if "Period" in stats.index else 0,
            "sharpe": round(stats.get("Sharpe Ratio", 0), 2),
            "max_drawdown_pct": round(stats.get("Max Drawdown [%]", 0), 2),
            "win_rate_pct": round(stats.get("Win Rate [%]", 0), 1),
            "num_trades": int(stats.get("Total Trades", 0)),
            "profit_factor": round(stats.get("Profit Factor", 0), 2),
            "avg_trade_pct": round(stats.get("Avg Winning Trade [%]", 0) * stats.get("Win Rate [%]", 0) / 100 - stats.get("Avg Losing Trade [%]", 0) * (100 - stats.get("Win Rate [%]", 0)) / 100, 2) if stats.get("Total Trades", 0) > 0 else 0,
        })

        # Collect daily returns for portfolio-level calc
        daily_ret = pf.daily_returns()
        daily_ret.name = ticker
        all_returns.append(daily_ret)

    asset_df = pd.DataFrame(results)

    # Portfolio-level: equal-weight daily returns across all assets
    if all_returns:
        port_returns = pd.concat(all_returns, axis=1).mean(axis=1)
        cum = (1 + port_returns).cumprod()
        years = len(port_returns) / 252
        total_ret = cum.iloc[-1] - 1
        cagr = (1 + total_ret) ** (1 / years) - 1
        sharpe = port_returns.mean() / port_returns.std() * np.sqrt(252) if port_returns.std() > 0 else 0
        rolling_max = cum.cummax()
        drawdown = (cum - rolling_max) / rolling_max
        max_dd = drawdown.min()

        portfolio_stats = {
            "total_return_pct": round(total_ret * 100, 2),
            "cagr_pct": round(cagr * 100, 2),
            "sharpe": round(sharpe, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "years": round(years, 1),
            "instruments": len(all_returns),
        }
    else:
        portfolio_stats = {}

    return asset_df, portfolio_stats


def print_report(asset_df, portfolio_stats):
    """Print formatted performance report."""
    print("=" * 80)
    print("BACKTEST REPORT — Trend Following (EMA 8/21 + ATR Filter)")
    print(f"Period: ~{portfolio_stats.get('years', 0)} years | Instruments: {portfolio_stats.get('instruments', 0)}")
    print(f"Initial equity: £{INIT_EQUITY:,} | Risk/trade: {RISK_PCT*100:.0f}% | Stop: {ATR_MULT}x ATR")
    print("=" * 80)

    print("\n📊 PORTFOLIO SUMMARY (equal-weight)")
    print("-" * 40)
    print(f"  CAGR:           {portfolio_stats.get('cagr_pct', 0):>8.2f}%")
    print(f"  Total Return:   {portfolio_stats.get('total_return_pct', 0):>8.2f}%")
    print(f"  Sharpe Ratio:   {portfolio_stats.get('sharpe', 0):>8.2f}")
    print(f"  Max Drawdown:   {portfolio_stats.get('max_drawdown_pct', 0):>8.2f}%")

    print("\n📈 PER-ASSET BREAKDOWN")
    print("-" * 80)
    print(f"{'Ticker':<10} {'Class':<12} {'Return%':>8} {'CAGR%':>7} {'Sharpe':>7} {'MaxDD%':>7} {'WinR%':>6} {'Trades':>7} {'PF':>5}")
    print("-" * 80)

    for _, row in asset_df.sort_values("total_return_pct", ascending=False).iterrows():
        print(f"{row['ticker']:<10} {row['asset_class']:<12} {row['total_return_pct']:>8.1f} {row['cagr_pct']:>7.1f} {row['sharpe']:>7.2f} {row['max_drawdown_pct']:>7.1f} {row['win_rate_pct']:>6.1f} {row['num_trades']:>7} {row['profit_factor']:>5.1f}")

    print("-" * 80)

    # Summary by asset class
    print("\n📋 BY ASSET CLASS")
    print("-" * 40)
    for ac, group in asset_df.groupby("asset_class"):
        avg_ret = group["total_return_pct"].mean()
        avg_sharpe = group["sharpe"].mean()
        print(f"  {ac:<15} avg return: {avg_ret:>7.1f}%  avg sharpe: {avg_sharpe:.2f}")

    print("\n" + "=" * 80)


def main():
    asset_df, portfolio_stats = run_backtest()
    print_report(asset_df, portfolio_stats)


if __name__ == "__main__":
    main()
