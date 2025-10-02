import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.fetchers.yahoo_fetcher import fetch
from strategies.moving_average import generate_signals

# Use Streamlit's caching to prevent re-downloading the stock list on every interaction.
@st.cache_data(ttl="1d") # Cache the data for one day
def get_omxs30_tickers():
    """
    Scrapes Wikipedia for the list of OMXS30 component stocks.
    Returns a list of Yahoo Finance compatible tickers (e.g., 'NDA-SE.ST').
    """
    try:
        # The URL for the Wikipedia page listing OMXS30 components
        url = "https://en.wikipedia.org/wiki/OMX_Stockholm_30"
        # pandas reads the HTML tables from the URL
        tables = pd.read_html(url)
        # The first table on the page is usually the one we need
        omx_df = tables[0]
        # The tickers are in the 'Ticker' column. We need to append '.ST' for Yahoo Finance.
        tickers = [f"{ticker.replace('.', '-')}.ST" for ticker in omx_df['Ticker']]
        return tickers
    except Exception as e:
        st.error(f"Failed to fetch OMXS30 tickers: {e}")
        return []

def plot_stock_chart(strategy_data, ticker_symbol):
    """
    Generates and returns a high-resolution Plotly figure for a single stock.
    """
    fig = go.Figure()

    # Plotting Close Price, SMAs, and Buy/Sell signals
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['Close'], name='Close Price', line=dict(color='skyblue')))
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_Short'], name='Short SMA', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_Long'], name='Long SMA', line=dict(color='purple')))
    
    buy_signals = strategy_data[strategy_data['Position'] == 2]
    fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['SMA_Short'], name='Buy Signal', mode='markers', marker=dict(symbol='triangle-up', color='green', size=12)))
    
    sell_signals = strategy_data[strategy_data['Position'] == -2]
    fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['SMA_Short'], name='Sell Signal', mode='markers', marker=dict(symbol='triangle-down', color='red', size=12)))

    # Increase graph size/resolution and update layout
    fig.update_layout(
        title=f'{ticker_symbol} Trading Signals',
        xaxis_title='Date',
        yaxis_title='Price (SEK)',
        legend_title='Legend',
        height=600  # Set a larger height for better resolution
    )
    return fig

def run_app():
    st.set_page_config(page_title="OMXS30 Trading Analysis", page_icon="🇸🇪", layout="wide")
    st.title("OMXS30 Intraday Strategy Analysis")
    st.caption("This tool analyzes stocks based on a 10/50 period Moving Average Crossover strategy.")

    if 'analyzed_stocks' not in st.session_state:
        st.session_state.analyzed_stocks = {}

    if st.button("Analyze OMXS30 Stocks", type="primary"):
        tickers = get_omxs30_tickers()
        if tickers:
            buy_recommendations = []
            progress_bar = st.progress(0, text="Starting analysis...")
            
            # Loop through all tickers, analyze them, and find buy signals
            for i, ticker in enumerate(tickers):
                progress_text = f"Analyzing {ticker} ({i+1}/{len(tickers)})..."
                progress_bar.progress((i + 1) / len(tickers), text=progress_text)
                
                try:
                    data = fetch(ticker)
                    if not data.empty:
                        strategy_data = generate_signals(data)
                        st.session_state.analyzed_stocks[ticker] = strategy_data
                        
                        # Check the last signal: Was it a buy?
                        last_position = strategy_data['Position'].iloc[-1]
                        if last_position == 2: # '2' indicates a recent cross from sell to buy
                            buy_recommendations.append({
                                'Ticker': ticker,
                                'Last Price': strategy_data['Close'].iloc[-1],
                                'Signal Time': strategy_data.index[strategy_data['Position'] == 2][-1]
                            })
                except Exception:
                    # Silently fail for tickers that don't load
                    continue

            progress_bar.empty()
            
            # Store recommendations in session state
            st.session_state.recommendations = pd.DataFrame(buy_recommendations)

    # --- Display the results after analysis ---
    if 'recommendations' in st.session_state and not st.session_state.recommendations.empty:
        st.subheader("Stocks with Recent 'Buy' Signals")
        st.info("These stocks have recently triggered a 'Buy' signal according to the crossover strategy, sorted by the most recent signal.")
        
        # Sort by the signal time, newest first
        recommendations_df = st.session_state.recommendations.sort_values(by='Signal Time', ascending=False)
        st.dataframe(recommendations_df, use_container_width=True)
    elif 'recommendations' in st.session_state:
        st.warning("No stocks are currently showing a 'Buy' signal based on the strategy.")

    # --- Interactive Graph Section ---
    if st.session_state.analyzed_stocks:
        st.subheader("View Detailed Stock Chart")
        
        # Dropdown to select any of the analyzed stocks
        selected_ticker = st.selectbox(
            "Select a stock to view its detailed chart:",
            options=sorted(st.session_state.analyzed_stocks.keys())
        )
        
        if selected_ticker:
            fig = plot_stock_chart(st.session_state.analyzed_stocks[selected_ticker], selected_ticker)
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    run_app()
