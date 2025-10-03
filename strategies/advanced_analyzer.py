import pandas as pd
import pandas_ta as ta
import yfinance as yf

def analyze_stock(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Performs an advanced analysis on stock data using multiple indicators,
    including a multi-timeframe check.
    """
    if data.empty:
        return data

    # --- Calculate Intraday Indicators ---
    data.ta.sma(length=10, append=True)
    data.ta.sma(length=50, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    data.ta.rsi(length=14, append=True)
    data.ta.obv(append=True)
    
    # --- Multi-Timeframe Analysis ---
    is_daily_uptrend = False # Default to false
    try:
        # Fetch daily data to check the long-term trend
        daily_data = yf.Ticker(ticker).history(period="1y", interval="1d")
        if not daily_data.empty:
            daily_data['SMA_50_daily'] = daily_data['Close'].ta.sma(50)
            # Check if last close price is above the 50-day moving average
            if not daily_data['SMA_50_daily'].empty:
                is_daily_uptrend = data['Close'].iloc[-1] > daily_data['SMA_50_daily'].iloc[-1]
    except Exception:
        # If daily data fails for any reason, we just proceed without it
        is_daily_uptrend = False

    # --- Create a "Signal Score" (now out of 5) ---
    data['Signal_Score'] = 0
    
    # Rule 1: Moving Average Crossover (+1)
    data.loc[data['SMA_10'] > data['SMA_50'], 'Signal_Score'] += 1
    
    # Rule 2: MACD Signal (+1)
    data.loc[data['MACDh_12_26_9'] > 0, 'Signal_Score'] += 1
    
    # Rule 3: RSI Signal (+1) - a value below 50 is not overbought
    data.loc[data['RSI_14'] < 50, 'Signal_Score'] += 1

    # Rule 4: OBV Signal (+1) - volume is confirming the trend
    data['OBV_SMA_10'] = data['OBV'].rolling(window=10).mean()
    data.loc[data['OBV'] > data['OBV_SMA_10'], 'Signal_Score'] += 1
    
    # Rule 5: Daily Trend Confirmation (+1 bonus point)
    if is_daily_uptrend:
        data['Signal_Score'] = data['Signal_Score'] + 1
    
    # --- Determine Final Recommendation ---
    def get_recommendation(score):
        if score >= 4: # Higher threshold for "Strong Buy"
            return "Strong Buy"
        elif score >= 2:
            return "Buy"
        else:
            return "Neutral/Sell"
            
    data['Recommendation'] = data['Signal_Score'].apply(get_recommendation)
    
    return data
