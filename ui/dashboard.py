import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import streamlit.components.v1 as components
import joblib

from data.fetchers.yfinance_fetcher import fetch_daily_bars
from strategies.advanced_analyzer import analyze_stock
from strategies.backtest import run_backtest

@st.cache_data
def get_nordic_indices():
    # ... (function is unchanged)
    pass

def plot_stock_chart(strategy_data, ticker_symbol):
    if strategy_data is None or len(strategy_data) < 2:
        # ... (error handling is unchanged)
        pass
    
    start_price, end_price = strategy_data['Close'].iloc[0], strategy_data['Close'].iloc[-1]
    percent_change = ((end_price / start_price) - 1) * 100 if start_price != 0 else 0
    change_color = "green" if percent_change >= 0 else "red"
    chart_title = f"{ticker_symbol} Analysis | Change: <span style='color:{change_color};'>{percent_change:.2f}%</span>"

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
    
    # --- FIX: Find Bollinger Band column names dynamically for plotting ---
    bbu_col = next((col for col in strategy_data.columns if col.startswith('BBU_')), None)
    bbm_col = next((col for col in strategy_data.columns if col.startswith('BBM_')), None)
    bbl_col = next((col for col in strategy_data.columns if col.startswith('BBL_')), None)

    if all([bbu_col, bbm_col, bbl_col]):
        fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data[bbu_col], name='Upper Band', line=dict(color='gray', dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data[bbl_col], name='Lower Band', line=dict(color='gray', dash='dash'), fill='tonexty', fillcolor='rgba(128,128,128,0.1)'), row=1, col=1)
        fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data[bbm_col], name='Middle Band', line=dict(color='gray', dash='dash')), row=1, col=1)

    # (The rest of the plotting traces are unchanged)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['Close'], name='Close Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_10'], name='Short SMA'), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['MACD_12_26_9'], name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['MACDs_12_26_9'], name='Signal Line'), row=2, col=1)
    fig.add_trace(go.Bar(x=strategy_data.index, y=strategy_data['MACDh_12_26_9'], name='Histogram'), row=2, col=1)

    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['RSI_14'], name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="blue", row=3, col=1)

    # (The rest of the function is unchanged)
    fig.update_layout(title_text=chart_title, height=800, showlegend=True)
    return fig

# (The rest of the dashboard.py file is unchanged from the last complete version)
# ...
