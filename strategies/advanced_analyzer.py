import pandas as pd
import pandas_ta as ta
from data.fetchers.finnhub_fetcher import fetch_daily_bars # Import our new function

def analyze_stock(intraday_data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Performs an advanced analysis using multiple indicators, including a multi-timeframe check.
    """
    if intraday_data.empty:
        return intraday_data

    # --- Calculate Intraday Indicators ---
    intraday_data.ta.sma(length=10, append=True)
    intraday_data.ta.sma(length=50, append=True)
    intraday_data.ta.macd(fast=12, slow=26, signal=9, append=True)
    intraday_data.ta.rsi(length=14, append=True)
    intraday_data.ta.obv(append=True)
    
    # --- Multi-Timeframe Analysis ---
    is_daily_uptrend = False
    try:
        daily_data = fetch_daily_bars(ticker, days=100) # Fetch last 100 days
        if not daily_data.empty:
            daily_data['SMA_50_daily'] = daily_data['Close'].ta.sma(50)
            if not daily_data['SMA_50_daily'].empty:
                is_daily_uptrend = intraday_data['Close'].iloc[-1] > daily_data['SMA_50_daily'].iloc[-1]
    except Exception:
        is_daily_uptrend = False

    # --- Create a "Signal Score" (out of 5) ---
    intraday_data['Signal_Score'] = 0
    intraday_data.loc[intraday_data['SMA_10'] > intraday_data['SMA_50'], 'Signal_Score'] += 1
    intraday_data.loc[intraday_data['MACDh_12_26_9'] > 0, 'Signal_Score'] += 1
    intraday_data.loc[intraday_data['RSI_14'] < 50, 'Signal_Score'] += 1
    intraday_data['OBV_SMA_10'] = intraday_data['OBV'].rolling(window=10).mean()
    intraday_data.loc[intraday_data['OBV'] > intraday_data['OBV_SMA_10'], 'Signal_Score'] += 1
    if is_daily_uptrend:
        intraday_data['Signal_Score'] += 1
    
    def get_recommendation(score):
        if score >= 4: return "Strong Buy"
        elif score >= 2: return "Buy"
        else: return "Neutral/Sell"
    intraday_data['Recommendation'] = intraday_data['Signal_Score'].apply(get_recommendation)
    
    return intraday_data
