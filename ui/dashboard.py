import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.fetchers.yahoo_fetcher import fetch
from strategies.moving_average import generate_signals

@st.cache_data
def get_omxs30_tickers():
    """
    Returns a hardcoded list of OMXS30 tickers.
    This is faster and more reliable than web scraping.
    """
    tickers = [
        'ERIC-B.ST', 'ADDT-B.ST', 'SCA-B.ST', 'AZN.ST', 'BOL.ST', 'SAAB-B.ST',
        'NDA-SE.ST', 'SKA-B.ST', 'TEL2-B.ST', 'HM-B.ST', 'TELIA.ST', 'NIBE-B.ST',
        'LIFCO-B.ST', 'SHB-A.ST', 'SEB-A.ST', 'ESSITY-B.ST', 'SWED-A.ST', 'EVO.ST',
        'SKF-B.ST', 'INDU-C.ST', 'SAND.ST', 'VOLV-B.ST', 'HEXA-B.ST', 'ABB.ST',
        'ASSA-B.ST', 'EPI-A.ST', 'INVE-B.ST', 'EQT.ST', 'ALFA.ST', 'ATCO-A.ST'
    ]
    return tickers

def plot_stock_chart(strategy_data, ticker_symbol):
    """
    Generates and returns a high-resolution Plotly figure for a single stock.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['Close'], name='Close Price', line=dict(color='skyblue')))
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_Short'], name='Short SMA', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_Long'], name='Long SMA', line=dict(color='purple')))
    
    buy_signals = strategy_data[strategy_data['Position'] == 2]
    fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['SMA_Short'], name='Buy Signal', mode='markers', marker=dict(symbol='triangle-up', color='green', size=12)))
    
    sell_signals = strategy_data[strategy_data['Position'] == -2]
    fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['SMA_Short'], name='Sell Signal', mode='markers', marker=dict(symbol='triangle-down', color='red', size=12)))

    fig.update_layout(title=f'{ticker_symbol} Trading Signals', xaxis_title='Date', yaxis_title='Price (SEK)', legend_title='Legend', height=600)
    return fig

def run_app():
    st.set_page_config(page_title="OMXS30 Trading Analysis", page_icon="🇸🇪", layout="wide")
    st.title("OMXS30 Intraday Strategy Dashboard")

    # --- Create two tabs for different functionalities ---
    tab1, tab2 = st.tabs(["📈 OMXS30 Screener", "🔍 Individual Stock Analysis"])

    # --- Tab 1: OMXS30 Market Screener ---
    with tab1:
        st.header("OMXS30 Market Screener")
        st.info("Click the button to analyze all 30 stocks in the index and find recent 'Buy' signals based on the Moving Average Crossover strategy.")

        if st.button("Analyze OMXS30 Stocks", type="primary"):
            tickers = get_omxs30_tickers()
            buy_recommendations = []
            progress_bar = st.progress(0, text="Starting analysis...")
            
            all_analyzed_data = {}
            for i, ticker in enumerate(tickers):
                progress_text = f"Analyzing {ticker} ({i+1}/{len(tickers)})..."
                progress_bar.progress((i + 1) / len(tickers), text=progress_text)
                
                try:
                    data = fetch(ticker)
                    if not data.empty:
                        strategy_data = generate_signals(data)
                        all_analyzed_data[ticker] = strategy_data
                        
                        last_position = strategy_data['Position'].iloc[-1]
                        if last_position == 2:
                            buy_recommendations.append({
                                'Ticker': ticker,
                                'Last Price': f"{strategy_data['Close'].iloc[-1]:.2f}",
                                'Signal Time': strategy_data.index[strategy_data['Position'] == 2][-1].strftime('%Y-%m-%d %H:%M')
                            })
                except Exception:
                    continue

            progress_bar.empty()
            
            st.session_state.recommendations = pd.DataFrame(buy_recommendations)
            st.session_state.analyzed_stocks = all_analyzed_data

        # Display results if they exist in the session state
        if 'recommendations' in st.session_state:
            st.subheader("Stocks with Recent 'Buy' Signals")
            if not st.session_state.recommendations.empty:
                recommendations_df = st.session_state.recommendations.sort_values(by='Signal Time', ascending=False)
                st.dataframe(recommendations_df, use_container_width=True)
            else:
                st.success("Analysis complete. No stocks are currently showing a 'Buy' signal based on the strategy.")

    # --- Tab 2: Individual Stock Search ---
    with tab2:
        st.header("Analyze a Single Stock")
        
        # Get the list of tickers for the dropdown
        omxs30_tickers = get_omxs30_tickers()
        
        # We combine a selectbox and a text input for flexibility
        st.write("Select a stock from the OMXS30 list or enter any other ticker below.")
        
        selected_ticker = st.selectbox("OMXS30 Stocks", options=[""] + omxs30_tickers)
        custom_ticker = st.text_input("Enter Custom Ticker (e.g., GOOGL, TSLA)").upper()
        
        # Prioritize the custom ticker if entered, otherwise use the selected one
        ticker_to_analyze = custom_ticker if custom_ticker else selected_ticker

        if ticker_to_analyze:
            try:
                with st.spinner(f"Fetching and analyzing {ticker_to_analyze}..."):
                    stock_data = fetch(ticker_to_analyze)
                    if not stock_data.empty:
                        strategy_data = generate_signals(stock_data)
                        
                        st.subheader(f"Chart for {ticker_to_analyze}")
                        fig = plot_stock_chart(strategy_data, ticker_to_analyze)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.subheader(f"Data for {ticker_to_analyze}")
                        st.dataframe(strategy_data)
                    else:
                        st.warning("No data found for this ticker. Please check the symbol.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    run_app()
