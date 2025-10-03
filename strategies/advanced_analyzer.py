import pandas as pd
import pandas_ta as ta
from data.fetchers.finnhub_fetcher import fetch_daily_bars

def analyze_stock(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Performs an advanced analysis on stock data using multiple indicators,
    including a multi-timeframe check.
    """
    if data.empty:
        return data

    data.ta.sma(length=10, append=True)
    data.ta.sma(length=50, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    data.ta.rsi(length=14, append=True)
    data.ta.obv(append=True)
    
    is_daily_uptrend = False
    try:
        daily_data = fetch_daily_bars(ticker, days=100)
        if not daily_data.empty:
            daily_data['SMA_50_daily'] = daily_data['Close'].ta.sma(50)
            if not daily_data['SMA_50_daily'].empty and not pd.isna(daily_data['SMA_50_daily'].iloc[-1]):
                is_daily_uptrend = data['Close'].iloc[-1] > daily_data['SMA_50_daily'].iloc[-1]
    except Exception:
        is_daily_uptrend = False

    data['Signal_Score'] = 0
    data.loc[data['SMA_10'] > data['SMA_50'], 'Signal_Score'] += 1
    data.loc[data['MACDh_12_26_9'] > 0, 'Signal_Score'] += 1
    data.loc[data['RSI_14'] < 50, 'Signal_Score'] += 1
    data['OBV_SMA_10'] = data['OBV'].rolling(window=10).mean()
    data.loc[data['OBV'] > data['OBV_SMA_10'], 'Signal_Score'] += 1
    if is_daily_uptrend:
        data['Signal_Score'] += 1
    
    def get_recommendation(score):
        if score >= 4: return "Strong Buy"
        elif score >= 2: return "Buy"
        else: return "Neutral/Sell"
    data['Recommendation'] = data['Signal_Score'].apply(get_recommendation)
    
    return data
