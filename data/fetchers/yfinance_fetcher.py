import yfinance as yf
import pandas as pd
import streamlit as st

def fetch_daily_bars(ticker, period="2y"):
    """Fetches daily OHLCV bars for a given ticker using yfinance."""
    data = yf.Ticker(ticker).history(period=period, interval="1d")
    
    if data.empty:
        return pd.DataFrame()
        
    data.rename(columns={
        "Open": "Open", "High": "High", "Low": "Low", 
        "Close": "Close", "Volume": "Volume"
    }, inplace=True, errors='ignore')

    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    if all(col in data.columns for col in required_cols):
        return data[required_cols]
    else:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_fx_rate(from_currency, to_currency):
    """Fetches the latest exchange rate between two currencies."""
    if from_currency == to_currency:
        return 1.0
    
    fx_ticker = f"{from_currency}{to_currency}=X"
    try:
        fx_data = yf.Ticker(fx_ticker).history(period="5d", interval="1d")
        if not fx_data.empty:
            return fx_data['Close'].iloc[-1]
    except Exception:
        return None
    return None
