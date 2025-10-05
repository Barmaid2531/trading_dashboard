import pandas as pd
import pandas_ta as ta
from data.fetchers.yfinance_fetcher import fetch_daily_bars

def analyze_stock(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Performs an advanced analysis on stock data using multiple indicators."""
    if data.empty:
        return data

    data.ta.sma(length=10, append=True)
    data.ta.sma(length=50, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    data.ta.rsi(length=14, append=True)
    data.ta.obv(append=True)
    data.ta.atr(length=14, append=True)

    is_daily_uptrend = data['SMA_10'].iloc[-1] > data['SMA_50'].iloc[-1]

    data['Signal_Score'] = 0
    data.loc[data['SMA_10'] > data['SMA_50'], 'Signal_Score'] += 1
    data.loc[data['MACDh_12_26_9'] > 0, 'Signal_Score'] += 1
    data.loc[data['RSI_14'] < 60, 'Signal_Score'] += 1
    data['OBV_SMA_10'] = data['OBV'].rolling(window=10).mean()
    data.loc[data['OBV'] > data['OBV_SMA_10'], 'Signal_Score'] += 1
    if is_daily_uptrend:
        data['Signal_Score'] += 1
    
    def get_recommendation(score):
        if score >= 4: return "Strong Buy"
        elif score >= 2: return "Buy"
        else: return "Neutral/Sell"
    data['Recommendation'] = data['Signal_Score'].apply(get_recommendation)

    atr_multiplier_sl = 2.0
    atr_multiplier_tp = 4.0
    data['Stop_Loss'] = data['Close'] - (data['ATRr_14'] * atr_multiplier_sl)
    data['Take_Profit'] = data['Close'] + (data['ATRr_14'] * atr_multiplier_tp)
    
    return data
