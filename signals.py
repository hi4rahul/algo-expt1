"""Signal generation — ATR trend filter + EMA crossover."""

import pandas as pd


def compute_atr(df, period=14):
    """Average True Range."""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def generate_signals(df, ema_fast=8, ema_slow=21, atr_period=14, atr_trend_period=50):
    """
    Generate daily trade signals.

    Entry LONG when:
      1. EMA fast crosses above EMA slow (crossover)
      2. ATR is rising (current ATR > ATR SMA) — confirms trending market

    Exit when:
      1. EMA fast crosses below EMA slow

    Returns DataFrame with signal column: 1 = long, 0 = flat.
    """
    close = df["close"]

    # EMAs
    ema_f = close.ewm(span=ema_fast, adjust=False).mean()
    ema_s = close.ewm(span=ema_slow, adjust=False).mean()

    # ATR trend filter: ATR above its own moving average = trending
    atr = compute_atr(df, atr_period)
    atr_ma = atr.rolling(atr_trend_period).mean()
    trending = atr > atr_ma

    # EMA crossover
    ema_long = ema_f > ema_s

    # Signal: long when EMA bullish AND market is trending
    signal = (ema_long & trending).astype(int)

    result = pd.DataFrame({
        "close": close,
        "ema_fast": ema_f,
        "ema_slow": ema_s,
        "atr": atr,
        "atr_ma": atr_ma,
        "trending": trending,
        "signal": signal,
    }, index=df.index)

    return result
