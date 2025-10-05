import streamlit as st
import finnhub
import pandas as pd
from datetime import datetime, timedelta

@st.cache_resource
def get_finnhub_client():
    api_key = st.secrets["finnhub"]["api_key"]
    return finnhub.Client(api_key=api_key)

def fetch_daily_bars_finnhub(ticker, days=365, **kwargs):
    """Fetches daily OHLCV bars for a given ticker using Finnhub."""
    client = get_finnhub_client()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    start_ts, end_ts = int(start_date.timestamp()), int(end_date.timestamp())
    
    res = client.stock_candles(ticker, 'D', start_ts, end_ts)
    
    if res['s'] != 'ok' or not res.get('c'):
        return pd.DataFrame()

    df = pd.DataFrame({'Open': res['o'], 'High': res['h'], 'Low': res['l'], 'Close': res['c'], 'Volume': res['v']})
    df.index = pd.to_datetime(res['t'], unit='s')
    return df
