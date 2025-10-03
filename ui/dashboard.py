import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from data.fetchers.yahoo_fetcher import fetch
from strategies.advanced_analyzer import analyze_stock
from strategies.backtest import run_backtest
# REMOVED: from bokeh.plotting import figure (No longer needed)

@st.cache_data
def get_omxs30_tickers():
    # ... (function is unchanged)
    tickers = [
        'ERIC-B.ST', 'ADDT-B.ST', 'SCA-B.ST', 'AZN.ST', 'BOL.ST', 'SAAB-B.ST', 'NDA-SE.ST', 'SKA-B.ST',
        'TEL2-B.ST', 'HM-B.ST', 'TELIA.ST', 'NIBE-B.ST', 'LIFCO-B.ST', 'SHB-A.ST', 'SEB-A.ST', 'ESSITY-B.ST',
        'SWED-A.ST', 'EVO.ST', 'SKF-B.ST', 'INDU-C.ST', 'SAND.ST', 'VOLV-B.ST', 'HEXA-B.ST', 'ABB.ST',
        'ASSA-B.ST', 'EPI-A.ST', 'INVE-B.ST', 'EQT.ST', 'ALFA.ST', 'ATCO-A.ST'
    ]
    return tickers

def plot_stock_chart(strategy_data, ticker_symbol):
    # ... (function is unchanged)
    if strategy_data is None or len(strategy_data) < 2:
        fig = go.Figure()
        fig.update_layout(title=f'{ticker_symbol} - Not Enough Data', xaxis_visible=False, yaxis_visible=False)
        return fig
    start_price = strategy_data['Close'].iloc[0]
    end_price = strategy_data['Close'].iloc[-1]
    percent_change = ((end_price / start_price) - 1) * 100 if start_price != 0 else 0
    change_color = "green" if percent_change >= 0 else "red"
    chart_title = f"{ticker_symbol} Analysis | Change: <span style='color:{change_color};'>{percent_change:.2f}%</span>"
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['Close'], name='Close Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_10'], name='Short SMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_50'], name='Long SMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['MACD_12_26_9'], name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['MACDs_12_26_9'], name='Signal Line'), row=2, col=1)
    fig.add_trace(go.Bar(x=strategy_data.index, y=strategy_data['MACDh_12_26_9'], name='Histogram'), row=2, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['RSI_14'], name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="blue", row=3, col=1)
    fig.update_layout(title_text=chart_title, height=800, showlegend=True)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    fig.update_xaxes(rangeslider_visible=True, row=1, col=1)
    return fig

def display_detailed_view(ticker):
    # ... (function is unchanged)
    try:
        with st.spinner(f"Fetching data for {ticker}..."):
            stock_data = fetch(ticker)
        if stock_data.empty:
            st.warning("No data found for this ticker.")
            return
        strategy_data = analyze_stock(stock_data, ticker)
        col1, col2 = st.columns([1, 3])
        with col1:
            st.subheader("Key Metrics")
            last_row = strategy_data.iloc[-1]
            st.metric("Last Price", f"{last_row['Close']:.2f} SEK")
            st.metric("RSI (14)", f"{last_row['RSI_14']:.2f}")
            st.metric("MACD Hist", f"{last_row['MACDh_12_26_9']:.2f}")
            st.metric("Signal Score", f"{int(last_row['Signal_Score'])}/5")
            st.info(f"Recommendation: **{last_row['Recommendation']}**")
        with col2:
            fig = plot_stock_chart(strategy_data, ticker)
            st.plotly_chart(fig, use_container_width=True)
        with st.expander("View Full Data and Signals"):
            st.dataframe(strategy_data)
    except Exception as e:
        st.error(f"An error occurred while analyzing {ticker}.")
        st.exception(e)

def run_app():
    st.set_page_config(page_title="Trading Dashboard", layout="wide")

    if 'portfolio' not in st.session_state: st.session_state.portfolio = []
    if 'watchlist' not in st.session_state: st.session_state.watchlist = []

    with st.sidebar:
        st.title("💹 Trading Dashboard")
        st.info("Advanced analysis using multiple technical indicators.")
        st.write("---")
        st.header("My Data")
        uploaded_file = st.file_uploader("Import Data (JSON)", type=['json'])
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                st.session_state.portfolio = data.get('portfolio', [])
                st.session_state.watchlist = data.get('watchlist', [])
                st.success("Data imported successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error importing file: {e}")
        if st.session_state.portfolio or st.session_state.watchlist:
            data_to_export = {"portfolio": st.session_state.portfolio, "watchlist": st.session_state.watchlist}
            export_json = json.dumps(data_to_export, indent=4)
            st.download_button("Export Data", export_json, "my_data.json", "application/json")
        st.write("---")
        st.warning("Disclaimer: Not financial advice.")

    st.title("Advanced Intraday Stock Analysis")

    tab_names = ["📈 Screener", "🔍 Individual Analysis", "💼 Portfolio", "🔭 Watchlist", "🧪 Backtester"]
    tabs = st.tabs(tab_names)

    with tabs[0]: # Screener
        # ... (code is unchanged)
        st.header("Find Strong Buy Signals (OMXS30)")
        if st.button("Analyze All OMXS30 Stocks", type="primary"):
            pass # Placeholder for brevity
        if 'recommendations' in st.session_state:
            pass # Placeholder for brevity

    with tabs[1]: # Individual Analysis
        # ... (code is unchanged)
        st.header("Deep-Dive on a Single Stock")
        custom_ticker = st.text_input("Enter Any Ticker (e.g., GOOGL, TSLA, BTC-USD)").upper()
        if custom_ticker:
            display_detailed_view(custom_ticker)
            
    with tabs[2]: # Portfolio
        # ... (code is unchanged)
        st.header("My Portfolio Tracker")
        pass # Placeholder for brevity

    with tabs[3]: # Watchlist
        # ... (code is unchanged)
        st.header("My Stock Watchlist")
        pass # Placeholder for brevity
    
    with tabs[4]: # Backtester
        st.header("Strategy Backtester")
        with st.form("backtest_form"):
            c1, c2, c3 = st.columns(3)
            ticker = c1.text_input("Ticker Symbol", "AAPL").upper()
            start_date = c2.date_input("Start Date", pd.to_datetime("2023-01-01"))
            end_date = c3.date_input("End Date", pd.to_datetime("2024-01-01"))
            if st.form_submit_button("Run Backtest"):
                with st.spinner(f"Running backtest for {ticker}..."):
                    try:
                        stats, plot = run_backtest(ticker, start_date, end_date)
                        if stats is not None:
                            st.success("Backtest complete!")
                            st.subheader("Performance Metrics")
                            st.write(stats)
                            st.subheader("Equity Curve & Trades")
                            # --- FIX: Use st.plotly_chart to display the new figure ---
                            st.plotly_chart(plot, use_container_width=True)
                        else:
                            st.error("Could not fetch data.")
                    except ValueError as e:
                        st.error(e)

if __name__ == "__main__":
    run_app()
