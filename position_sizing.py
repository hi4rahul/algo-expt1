"""Position sizing — fixed % risk per trade, volatility-scaled via ATR."""

import pandas as pd


def size_position(price, atr, account_equity, risk_pct=0.01, atr_multiplier=2.0, max_position_pct=0.10):
    """
    Calculate position size based on ATR-scaled risk.

    Logic:
      - Risk per trade = account_equity * risk_pct (e.g. 1% of £50k = £500)
      - Stop distance = ATR * atr_multiplier (e.g. 2x ATR)
      - Shares = risk_amount / stop_distance
      - Cap at max_position_pct of equity

    Returns dict with shares, position_value, stop_price, risk_amount.
    Returns None if inputs are invalid.
    """
    if pd.isna(price) or pd.isna(atr) or atr <= 0 or price <= 0:
        return None

    risk_amount = account_equity * risk_pct
    stop_distance = atr * atr_multiplier
    shares = int(risk_amount / stop_distance)

    if shares <= 0:
        return None

    position_value = shares * price
    max_value = account_equity * max_position_pct

    # Cap position size
    if position_value > max_value:
        shares = int(max_value / price)
        position_value = shares * price

    if shares <= 0:
        return None

    return {
        "shares": shares,
        "position_value": round(position_value, 2),
        "stop_price": round(price - stop_distance, 4),
        "stop_distance": round(stop_distance, 4),
        "risk_amount": round(shares * stop_distance, 2),
    }
