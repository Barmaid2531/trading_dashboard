import pandas as pd
import pandas_ta as ta

def analyze_stock(data: pd.DataFrame) -> pd.DataFrame:
    """
    Performs an advanced analysis on stock data using multiple indicators.
    
    Args:
        data: DataFrame with stock prices (OHLCV).
        
    Returns:
        The input DataFrame with many new indicator and signal columns.
    """
    if data.empty:
        return data

    # Use pandas_ta to calculate multiple indicators at once
    # This is a flexible way to add any of the 100+ indicators from the library
    data.ta.strategy("All",
        # Moving Averages
        sma_fast=10, sma_slow=50,
        # MACD
        macd_fast=12, macd_slow=26, macd_signal=9,
        # RSI
        rsi_length=14,
        # On-Balance Volume
        obv=True
    )
    
    # --- Create a "Signal Score" based on indicator conditions ---
    data['Signal_Score'] = 0
    
    # 1. Moving Average Crossover (+1 for buy signal)
    data.loc[data['SMA_10'] > data['SMA_50'], 'Signal_Score'] += 1
    
    # 2. MACD Signal (+1 for buy signal)
    # MACDh is the MACD histogram. A positive value is bullish.
    data.loc[data['MACDh_12_26_9'] > 0, 'Signal_Score'] += 1
    
    # 3. RSI Signal (+1 for buy signal)
    # We'll consider RSI moving up from a low level as bullish.
    data.loc[data['RSI_14'] < 50, 'Signal_Score'] += 1

    # 4. OBV Signal (+1 for buy signal)
    # A simple check: is the OBV trending up? (using a moving average of OBV)
    data['OBV_SMA_10'] = data['OBV'].rolling(window=10).mean()
    data.loc[data['OBV'] > data['OBV_SMA_10'], 'Signal_Score'] += 1
    
    # --- Determine Final Recommendation ---
    def get_recommendation(score):
        if score >= 3:
            return "Strong Buy"
        elif score == 2:
            return "Buy"
        else:
            return "Neutral/Sell"
            
    data['Recommendation'] = data['Signal_Score'].apply(get_recommendation)
    
    return data
