import pandas as pd

def calculate_bollinger(series: pd.Series, window: int = 20, num_std: int = 2):
    """
    Calculate Bollinger Bands.
    
    Parameters:
        series (pd.Series): Price series (usually Close prices).
        window (int): Lookback window size.
        num_std (int): Number of standard deviations.
    
    Returns:
        tuple: (upper_band, lower_band)
    """
    rolling_mean = series.rolling(window).mean()
    rolling_std = series.rolling(window).std()
    
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)
    
    return upper_band, lower_band
