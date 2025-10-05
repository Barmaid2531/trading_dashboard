import yfinance as yf
import pandas as pd

def fetch_daily_bars(ticker, period="2y"):
    """Fetches daily OHLCV bars for a given ticker using yfinance."""
    data = yf.Ticker(ticker).history(period=period, interval="1d")
    
    if data.empty:
        return pd.DataFrame()
        
    # Ensure column names are standardized
    data.rename(columns={
        "Open": "Open", "High": "High", "Low": "Low", 
        "Close": "Close", "Volume": "Volume"
    }, inplace=True, errors='ignore')

    # Drop columns that are not needed to avoid issues
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    if all(col in data.columns for col in required_cols):
        return data[required_cols]
    else:
        return pd.DataFrame()
