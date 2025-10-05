import pandas as pd
import pandas_ta as ta
from data.fetchers.yfinance_fetcher import fetch_daily_bars

def analyze_stock(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Performs an advanced analysis on stock data, including a multi-timeframe
    and relative strength check.
    """
    if data.empty or len(data) < 50: # Need enough data for calculations
        return pd.DataFrame()

    # --- Calculate Standard Indicators ---
    data.ta.sma(length=10, append=True)
    data.ta.sma(length=50, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    data.ta.rsi(length=14, append=True)
    data.ta.obv(append=True)
    data.ta.atr(length=14, append=True)
    
    # --- NEW: Relative Strength Analysis ---
    is_outperforming = False
    try:
        # Determine the market index based on the ticker's suffix
        if ticker.endswith('.ST'): market_index = '^OMX'
        elif ticker.endswith('.CO'): market_index = '^OMXC25'
        elif ticker.endswith('.HE'): market_index = '^OMXH25'
        elif ticker.endswith('.OL'): market_index = 'OBX.OL'
        else: market_index = 'SPY' # Default to S&P 500 for US stocks

        index_data = fetch_daily_bars(market_index, period="3mo")
        if not index_data.empty:
            # Calculate 20-day performance for both
            stock_performance = data['Close'].pct_change(20).iloc[-1]
            index_performance = index_data['Close'].pct_change(20).iloc[-1]
            
            data['Relative_Strength'] = stock_performance - index_performance
            is_outperforming = stock_performance > index_performance
    except Exception:
        is_outperforming = False

    # --- Create a "Signal Score" (now out of 6) ---
    data['Signal_Score'] = 0
    data.loc[data['SMA_10'] > data['SMA_50'], 'Signal_Score'] += 1
    data.loc[data['MACDh_12_26_9'] > 0, 'Signal_Score'] += 1
    data.loc[data['RSI_14'] < 60, 'Signal_Score'] += 1
    data['OBV_SMA_10'] = data['OBV'].rolling(window=10).mean()
    data.loc[data['OBV'] > data['OBV_SMA_10'], 'Signal_Score'] += 1
    if data['SMA_10'].iloc[-1] > data['SMA_50'].iloc[-1]: # Daily trend check
        data['Signal_Score'] += 1
    if is_outperforming: # Relative strength check
        data['Signal_Score'] += 1
    
    def get_recommendation(score):
        if score >= 5: return "Strong Buy"
        elif score >= 3: return "Buy"
        else: return "Neutral/Sell"
    data['Recommendation'] = data['Signal_Score'].apply(get_recommendation)

    # Risk Management Calculations
    atr_multiplier_sl, atr_multiplier_tp = 2.0, 4.0
    data['Stop_Loss'] = data['Close'] - (data['ATRr_14'] * atr_multiplier_sl)
    data['Take_Profit'] = data['Close'] + (data['ATRr_14'] * atr_multiplier_tp)
    
    return data
