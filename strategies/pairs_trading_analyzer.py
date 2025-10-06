import pandas as pd
from statsmodels.tsa.stattools import coint
from data.fetchers.yfinance_fetcher import fetch_daily_bars
import streamlit as st

@st.cache_data
def find_cointegrated_pairs(tickers):
    """
    Scans a list of tickers to find cointegrated pairs.
    """
    # yfinance allows fetching multiple tickers at once
    data = fetch_daily_bars(tickers, period="5y")
    if data.empty or not isinstance(data['Close'], pd.DataFrame):
        st.warning("Could not fetch data for multiple tickers at once for pair analysis.")
        return pd.DataFrame()
        
    close_prices = data['Close']
    keys = close_prices.columns
    pairs = []
    
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            ticker1, ticker2 = keys[i], keys[j]
            
            price_series1 = close_prices[ticker1].dropna()
            price_series2 = close_prices[ticker2].dropna()
            
            if len(price_series1) < 252 or len(price_series2) < 252:
                continue

            common_index = price_series1.index.intersection(price_series2.index)
            if len(common_index) < 252:
                continue
                
            price_series1 = price_series1.loc[common_index]
            price_series2 = price_series2.loc[common_index]
            
            score, pvalue, _ = coint(price_series1, price_series2)
            
            if pvalue < 0.05:
                pairs.append({'Pair': f"{ticker1}-{ticker2}", 'P-Value': pvalue})
    
    return pd.DataFrame(pairs)

def analyze_pair_spread(ticker1, ticker2):
    """
    Analyzes the spread of a cointegrated pair and calculates the Z-score.
    """
    data = fetch_daily_bars([ticker1, ticker2], period="1y")
    if data.empty or not isinstance(data['Close'], pd.DataFrame) or len(data['Close'].columns) < 2:
        return pd.DataFrame()
        
    close_prices = data['Close']
    
    spread = close_prices[ticker1] / close_prices[ticker2]
    
    mean = spread.rolling(window=20).mean()
    std = spread.rolling(window=20).std()
    z_score = (spread - mean) / std
    
    analysis_df = pd.DataFrame({'Spread': spread, 'Z_Score': z_score})
    
    return analysis_df
