# indicators/bollinger.py
import pandas as pd
from typing import Tuple

def calculate_bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands (upper, lower) for a close price series.
    Returns (upper_band, lower_band)
    """
    ma = close.rolling(window=period, min_periods=period).mean()
    std = close.rolling(window=period, min_periods=period).std()
    upper_band = ma + std_dev * std
    lower_band = ma - std_dev * std
    return upper_band, lower_band
