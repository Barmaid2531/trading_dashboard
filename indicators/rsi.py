# indicators/rsi.py
import pandas as pd

def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate RSI from a pandas Series of close prices.
    Returns a pandas Series aligned with input (NaNs for first `period` rows).
    """
    close = close.astype(float)
    delta = close.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    # Use exponential moving average (more responsive) or simple rolling as desired.
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    # Avoid division by zero
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi
