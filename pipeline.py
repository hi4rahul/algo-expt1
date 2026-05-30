"""Stage 1 — Download, clean, align, and validate historical OHLCV data."""

import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from universe import UNIVERSE, get_tickers

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
YEARS = 10


def download_all():
    """Download 10 years of daily OHLCV for all instruments."""
    os.makedirs(DATA_DIR, exist_ok=True)
    end = datetime.today()
    start = end - timedelta(days=YEARS * 365)

    tickers = get_tickers()
    print(f"Downloading {len(tickers)} instruments from {start.date()} to {end.date()}...")

    # yfinance batch download — adjusted close used as default
    raw = yf.download(tickers, start=start, end=end, group_by="ticker", auto_adjust=True)
    return raw


def clean_and_align(raw):
    """Clean data: handle missing values, align to common date index."""
    tickers = get_tickers()
    frames = {}

    for ticker in tickers:
        try:
            if len(tickers) > 1:
                df = raw[ticker].copy()
            else:
                df = raw.copy()
        except KeyError:
            print(f"  ⚠️  {ticker}: no data returned")
            continue

        # Drop rows where all OHLCV are NaN
        df = df.dropna(how="all")

        if df.empty:
            print(f"  ⚠️  {ticker}: empty after dropping NaN rows")
            continue

        # Forward-fill small gaps (weekends already excluded, this catches holidays)
        df = df.ffill(limit=5)

        # Drop any remaining NaN rows at the start (before first valid data)
        df = df.dropna()

        # Ensure standard columns
        df.columns = [c.lower() for c in df.columns]
        expected = ["open", "high", "low", "close", "volume"]
        df = df[[c for c in expected if c in df.columns]]

        frames[ticker] = df

    # Build common date index (union of all dates)
    all_dates = sorted(set().union(*(df.index for df in frames.values())))
    common_index = pd.DatetimeIndex(all_dates)

    # Reindex each frame to common dates, forward-fill gaps up to 5 days
    aligned = {}
    for ticker, df in frames.items():
        df = df.reindex(common_index)
        df = df.ffill(limit=5)
        aligned[ticker] = df

    return aligned


def save_parquet(aligned):
    """Save each instrument as a parquet file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    for ticker, df in aligned.items():
        safe_name = ticker.replace(".", "_")
        path = os.path.join(DATA_DIR, f"{safe_name}.parquet")
        df.to_parquet(path)
    print(f"  ✅ Saved {len(aligned)} parquet files to {DATA_DIR}/")


def validate(aligned):
    """Print validation report. NaN% measured only within each instrument's valid range."""
    print("\n" + "=" * 70)
    print("VALIDATION REPORT")
    print("=" * 70)
    print(f"{'Ticker':<12} {'Rows':>6} {'Start':<12} {'End':<12} {'NaN%':>6} {'Status'}")
    print("-" * 70)

    issues = []
    for ticker in get_tickers():
        if ticker not in aligned:
            print(f"{ticker:<12} {'—':>6} {'—':<12} {'—':<12} {'—':>6} ❌ MISSING (not on yfinance)")
            issues.append(ticker)
            continue

        df = aligned[ticker]
        # Trim to instrument's own valid range (first non-NaN to last non-NaN)
        valid = df.dropna(how="all")
        if valid.empty:
            print(f"{ticker:<12} {'—':>6} {'—':<12} {'—':<12} {'—':>6} ❌ NO VALID DATA")
            issues.append(ticker)
            continue

        rows = len(valid)
        start = valid.index.min().strftime("%Y-%m-%d")
        end = valid.index.max().strftime("%Y-%m-%d")
        nan_pct = valid.isna().sum().sum() / (rows * len(valid.columns)) * 100

        status = "✅" if nan_pct < 5 and rows > 200 else "⚠️"
        if status == "⚠️":
            issues.append(ticker)

        print(f"{ticker:<12} {rows:>6} {start:<12} {end:<12} {nan_pct:>5.1f}% {status}")

    print("-" * 70)
    print(f"Total: {len(aligned)}/{len(get_tickers())} instruments loaded")
    if issues:
        print(f"⚠️  Issues: {', '.join(issues)}")
    else:
        print("✅ All instruments ready for signal generation")
    print("=" * 70)


def main():
    raw = download_all()
    aligned = clean_and_align(raw)
    save_parquet(aligned)
    validate(aligned)


if __name__ == "__main__":
    main()
