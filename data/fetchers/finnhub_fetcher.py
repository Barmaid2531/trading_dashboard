import streamlit as st
import finnhub
import pandas as pd
from datetime import datetime, timedelta

@st.cache_resource
def get_finnhub_client():
    """Initializes the Finnhub client using the API key from secrets."""
    api_key = st.secrets["finnhub"]["api_key"]
    return finnhub.Client(api_key=api_key)

@st.cache_data(ttl="1d")
def get_nordic_assets():
    """Fetches a list of all symbols from Nordic markets using Finnhub."""
    client = get_finnhub_client()
    exchanges = ['ST', 'CO', 'HE'] # Stockholm, Copenhagen, Helsinki
    all_assets = []
    
    for ex in exchanges:
        symbols = client.stock_symbols(ex)
        for s in symbols:
            if s['mic'] and s['displaySymbol']: # Ensure essential data exists
                s['exchange'] = ex
                all_assets.append(s)
            
    asset_list = [{'symbol': a['displaySymbol'], 'name': a['description'], 'exchange': a['exchange']} for a in all_assets]
    return asset_list

def fetch_daily_bars(ticker, days=365):
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
