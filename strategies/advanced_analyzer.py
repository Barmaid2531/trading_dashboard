import pandas as pd
import pandas_ta as ta
from data.fetchers.yfinance_fetcher import fetch_daily_bars

def analyze_stock(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Performs an advanced analysis on stock data using multiple indicators."""
    if data.empty or len(data) < 50:
        return pd.DataFrame()

    data.ta.sma(length=10, append=True)
    data.ta.sma(length=50, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    data.ta.rsi(length=14, append=True)
    data.ta.obv(append=True)
    data.ta.atr(length=14, append=True)
    data.ta.bbands(length=20, append=True)
    
    is_outperforming = False
    try:
        if ticker.endswith('.ST'): market_index = '^OMX'
        else: market_index = 'SPY'
        index_data = fetch_daily_bars(market_index, period="3mo")
        if not index_data.empty:
            stock_performance = data['Close'].pct_change(20).iloc[-1]
            index_performance = index_data['Close'].pct_change(20).iloc[-1]
            data['Relative_Strength'] = stock_performance - index_performance
            if pd.notna(stock_performance) and pd.notna(index_performance):
                is_outperforming = stock_performance > index_performance
    except Exception:
        is_outperforming = False

    data['Signal_Score'] = 0
    data.loc[data['SMA_10'] > data['SMA_50'], 'Signal_Score'] += 1
    data.loc[data['MACDh_12_26_9'] > 0, 'Signal_Score'] += 1
    data.loc[data['RSI_14'] < 60, 'Signal_Score'] += 1
    data['OBV_SMA_10'] = data['OBV'].rolling(window=10).mean()
    data.loc[data['OBV'] > data['OBV_SMA_10'], 'Signal_Score'] += 1
    if data['SMA_10'].iloc[-1] > data['SMA_50'].iloc[-1]: data['Signal_Score'] += 1
    if is_outperforming: data['Signal_Score'] += 1
    bbm_col = next((col for col in data.columns if col.startswith('BBM_')), None)
    if bbm_col and not data[bbm_col].empty:
        data.loc[data['Close'] > data[bbm_col], 'Signal_Score'] += 1
    
    def get_recommendation(score):
        if score >= 5: return "Strong Buy"
        elif score >= 3: return "Buy"
        else: return "Neutral/Sell"
    data['Recommendation'] = data['Signal_Score'].apply(get_recommendation)

    atr_multiplier_sl, atr_multiplier_tp = 2.0, 4.0
    data['Stop_Loss'] = data['Close'] - (data['ATRr_14'] * atr_multiplier_sl)
    data['Take_Profit'] = data['Close'] + (data['ATRr_14'] * atr_multiplier_tp)
    
    return data

def analyze_stock_ml(data: pd.DataFrame, model):
    """Calculates features and uses a trained ML model for predictions."""
    if data.empty or model is None:
        return data
    data.ta.strategy("All", sma_fast=10, sma_slow=50, macd_fast=12, macd_slow=26, macd_signal=9, rsi_length=14, obv=True)
    data = data.dropna()
    if data.empty:
        return data
    last_row = data.iloc[[-1]]
    features = last_row.select_dtypes(include=['number'])
    model_features = model.get_booster().feature_names
    features = features.reindex(columns=model_features, fill_value=0)
    prediction = model.predict(features)[0]
    prediction_proba = model.predict_proba(features)[0][1]
    data['ML_Prediction'] = prediction
    data['ML_Confidence'] = prediction_proba
    return data
