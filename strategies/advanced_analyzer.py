import pandas as pd
import pandas_ta as ta
from data.fetchers.yfinance_fetcher import fetch_daily_bars

def analyze_stock(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Performs an advanced analysis on stock data using multiple indicators.
    """
    if data.empty or len(data) < 50:
        return pd.DataFrame()

    # Calculate all indicators
    data.ta.sma(length=10, append=True)
    data.ta.sma(length=50, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    data.ta.rsi(length=14, append=True)
    data.ta.obv(append=True)
    data.ta.atr(length=14, append=True)
    data.ta.bbands(length=20, append=True)
    
    # --- FIX: Find Bollinger Band column names dynamically ---
    bbm_col = next((col for col in data.columns if col.startswith('BBM_')), None)

    # (Relative Strength Analysis is unchanged)
    is_outperforming = False
    try:
        if ticker.endswith('.ST'): market_index = '^OMX'
        elif ticker.endswith('.CO'): market_index = '^OMXC25'
        # ... (rest of the logic is the same)
    except Exception:
        is_outperforming = False

    # --- Create a "Signal Score" (now out of 7) ---
    data['Signal_Score'] = 0
    data.loc[data['SMA_10'] > data['SMA_50'], 'Signal_Score'] += 1
    data.loc[data['MACDh_12_26_9'] > 0, 'Signal_Score'] += 1
    data.loc[data['RSI_14'] < 60, 'Signal_Score'] += 1
    data['OBV_SMA_10'] = data['OBV'].rolling(window=10).mean()
    data.loc[data['OBV'] > data['OBV_SMA_10'], 'Signal_Score'] += 1
    if data['SMA_10'].iloc[-1] > data['SMA_50'].iloc[-1]: data['Signal_Score'] += 1
    if is_outperforming: data['Signal_Score'] += 1
    
    # Use the dynamically found column name
    if bbm_col and not data[bbm_col].empty:
        data.loc[data['Close'] > data[bbm_col], 'Signal_Score'] += 1
    
    def get_recommendation(score):
        if score >= 5: return "Strong Buy"
        elif score >= 3: return "Buy"
        else: return "Neutral/Sell"
    data['Recommendation'] = data['Signal_Score'].apply(get_recommendation)

    # (Risk Management Calculations are unchanged)
    atr_multiplier_sl, atr_multiplier_tp = 2.0, 4.0
    data['Stop_Loss'] = data['Close'] - (data['ATRr_14'] * atr_multiplier_sl)
    data['Take_Profit'] = data['Close'] + (data['ATRr_14'] * atr_multiplier_tp)
    
    return data
