import yfinance as yf
import pandas as pd

def fetch(ticker_symbol: str) -> pd.DataFrame:
    """
    Fetches intraday stock data for a given ticker symbol.
    
    Args:
        ticker_symbol: The stock ticker (e.g., 'AAPL').
        
    Returns:
        A pandas DataFrame with 5-minute interval stock data for the last 5 days.
    """
    ticker = yf.Ticker(ticker_symbol)
    
    # Fetch intraday data for the last 5 days at a 5-minute interval.
    # Note: Yahoo Finance limits intraday data to the last 60 days.
    # period="5d" -> 5 days
    # interval="5m" -> 5 minutes
    data = ticker.history(period="5d", interval="5m")
    
    return data
