import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_daily_bars_yfinance(ticker, days=365, **kwargs):
    """Fetches daily OHLCV bars for a given ticker using yfinance."""
    # yfinance uses a period string like "1y", "2y"
    period = f"{int(days / 365.25 * 12)}mo" if days > 60 else f"{days}d"
    
    data = yf.Ticker(ticker).history(period=period, interval="1d")
    
    if data.empty:
        return pd.DataFrame()
        
    data.rename(columns={
        "Open": "Open", "High": "High", "Low": "Low", 
        "Close": "Close", "Volume": "Volume"
    }, inplace=True, errors='ignore')

    return data[['Open', 'High', 'Low', 'Close', 'Volume']]
