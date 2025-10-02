import pandas as pd

def generate_signals(data: pd.DataFrame) -> pd.DataFrame:
    """
    Generates trading signals based on a Moving Average Crossover strategy.
    
    Args:
        data: DataFrame with stock prices, must contain a 'Close' column.
        
    Returns:
        The input DataFrame with added columns for moving averages and signals.
    """
    if data.empty:
        return data

    # --- 1. Define the moving average windows ---
    # A short-term window (e.g., 10 periods) and a long-term window (e.g., 50 periods).
    # A "period" here is 5 minutes, based on our data interval.
    short_window = 10  # 10 * 5 minutes = 50 minutes
    long_window = 50   # 50 * 5 minutes = 4.16 hours
    
    # --- 2. Calculate the Simple Moving Averages (SMA) ---
    data['SMA_Short'] = data['Close'].rolling(window=short_window, min_periods=1).mean()
    data['SMA_Long'] = data['Close'].rolling(window=long_window, min_periods=1).mean()
    
    # --- 3. Generate the trading signals ---
    # Create a 'Signal' column, initially with no signal (0).
    data['Signal'] = 0
    
    # When the short SMA crosses above the long SMA, it's a "Buy" signal (1).
    data.loc[data['SMA_Short'] > data['SMA_Long'], 'Signal'] = 1
    
    # When the short SMA crosses below the long SMA, it's a "Sell" signal (-1).
    data.loc[data['SMA_Short'] < data['SMA_Long'], 'Signal'] = -1

    # --- 4. Find the exact crossover points for visualization ---
    # We only want to plot a marker on the chart at the moment the crossover happens.
    data['Position'] = data['Signal'].diff()

    return data