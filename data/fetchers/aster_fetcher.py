import pandas as pd
from .finnhub_fetcher import fetch_daily_bars_finnhub
from .yfinance_fetcher import fetch_daily_bars_yfinance

def fetch_data(ticker, **kwargs):
    """
    Fetches data from the primary source (Finnhub) and falls back to the
    secondary source (yfinance) if the primary fails.
    """
    try:
        # 1. Try fetching from Finnhub first
        data = fetch_daily_bars_finnhub(ticker, **kwargs)
        if not data.empty:
            data['Source'] = 'Finnhub'
            return data
    except Exception:
        # If Finnhub fails for any reason, we'll proceed to the fallback
        pass

    # 2. If Finnhub fails, try yfinance as a fallback
    try:
        data = fetch_daily_bars_yfinance(ticker, **kwargs)
        if not data.empty:
            data['Source'] = 'yfinance'
            return data
    except Exception:
        pass

    # 3. If both fail, return an empty DataFrame
    return pd.DataFrame()
