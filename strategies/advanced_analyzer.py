import pandas as pd
import pandas_ta as ta

def analyze_stock(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    # ... (existing indicator calculations) ...

    # Fetch daily data to check the long-term trend
    daily_data = yf.download(ticker, period="1y", interval="1d", progress=False)
    daily_data['SMA_50_daily'] = daily_data['Close'].ta.sma(50)
    
    # --- Create a "Signal Score" ---
    data['Signal_Score'] = 0
    # ... (existing scoring logic) ...

    # Add a bonus point if the daily trend is also up
    if not daily_data.empty and data['Close'].iloc[-1] > daily_data['SMA_50_daily'].iloc[-1]:
        data['Signal_Score'] += 1 # This would change the max score to 5

    """
    Performs an advanced analysis on stock data using multiple indicators.
    """
    if data.empty:
        return data

    # --- Calculate Indicators Individually (More Robust) ---
    # The append=True argument adds the results as new columns to the DataFrame
    data.ta.sma(length=10, append=True)
    data.ta.sma(length=50, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    data.ta.rsi(length=14, append=True)
    data.ta.obv(append=True)
    
    # --- Create a "Signal Score" based on indicator conditions ---
    data['Signal_Score'] = 0
    
    # 1. Moving Average Crossover (+1 for buy signal)
    data.loc[data['SMA_10'] > data['SMA_50'], 'Signal_Score'] += 1
    
    # 2. MACD Signal (+1 for buy signal)
    data.loc[data['MACDh_12_26_9'] > 0, 'Signal_Score'] += 1
    
    # 3. RSI Signal (+1 for buy signal)
    data.loc[data['RSI_14'] < 50, 'Signal_Score'] += 1

    # 4. OBV Signal (+1 for buy signal)
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
    # ... (rest of the function) ...
