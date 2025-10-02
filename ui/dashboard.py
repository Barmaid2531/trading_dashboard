import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.fetchers.yahoo_fetcher import fetch
from strategies.moving_average import generate_signals

@st.cache_data
def get_omxs30_tickers():
    """Returns a hardcoded list of OMXS30 tickers."""
    tickers = [
        'ERIC-B.ST', 'ADDT-B.ST', 'SCA-B.ST', 'AZN.ST', 'BOL.ST', 'SAAB-B.ST',
        'NDA-SE.ST', 'SKA-B.ST', 'TEL2-B.ST', 'HM-B.ST', 'TELIA.ST', 'NIBE-B.ST',
        'LIFCO-B.ST', 'SHB-A.ST', 'SEB-A.ST', 'ESSITY-B.ST', 'SWED-A.ST', 'EVO.ST',
        'SKF-B.ST', 'INDU-C.ST', 'SAND.ST', 'VOLV-B.ST', 'HEXA-B.ST', 'ABB.ST',
        'ASSA-B.ST', 'EPI-A.ST', 'INVE-B.ST', 'EQT.ST', 'ALFA.ST', 'ATCO-A.ST'
    ]
    return tickers

def plot_stock_chart(strategy_data, ticker_symbol):
    """Generates a high-resolution Plotly figure for a single stock."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['Close'], name='Close Price', line=dict(color='skyblue')))
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_Short'], name='Short SMA', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_Long'], name='Long SMA', line=dict(color='purple')))
    
    buy_signals = strategy_data[strategy_data['Position'] == 2]
    fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['SMA_Short'], name='Buy Signal', mode='markers', marker=dict(symbol='triangle-up', color='green', size=12)))
    
    sell_signals = strategy_data[strategy_data['Position'] == -2]
    fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['SMA_Short'], name='Sell Signal', mode='markers', marker=dict(symbol='triangle-down', color='red', size=12)))

    fig.update_layout(title=f'{ticker_symbol} Trading Signals', xaxis_title='Date', yaxis_title='Price (SEK)', legend_title='Legend', height=500)
    return fig

def run_app():
    st.set_page_config(page_title="Trading Dashboard", page_icon="💹", layout="wide")

    # --- Sidebar ---
    with st.sidebar:
        st.title("💹 Trading Dashboard")
        st.info("This app analyzes the OMXS30 index using a Moving Average Crossover strategy to identify potential intraday buy signals.")
        st.write("---")
        st.write("Strategy: Buy when the short-term (10-period) moving average crosses above the long-term (50-period) one.")
        st.warning("Disclaimer: This is an educational tool and not financial advice.")

    # --- Main Page Title ---
    st.title("OMXS30 Intraday Analysis")

    # --- Tabs for different functionalities ---
    tab1, tab2 = st.tabs(["📈 OMXS30 Screener", "🔍 Individual Stock Analysis"])

    # --- Tab 1: OMXS30 Market Screener ---
    with tab1:
        st.header("Find Recent Buy Signals")
        
        if st.button("Analyze All OMXS30 Stocks", type="primary"):
            # ... (Analysis logic remains the same)
            tickers = get_omxs30_tickers()
            buy_recommendations = []
            progress_bar = st.progress(0, text="Starting analysis...")
            
            for i, ticker in enumerate(tickers):
                # ... (Loop logic is the same)
                try:
                    data = fetch(ticker)
                    if not data.empty:
                        strategy_data = generate_signals(data)
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

        if 'recommendations' in st.session_state:
            recommendations_df = st.session_state.recommendations
            st.metric(label="Stocks with Buy Signals", value=len(recommendations_df))
            
            if not recommendations_df.empty:
                st.success("Displaying stocks with the most recent 'Buy' signals.")
                sorted_df = recommendations_df.sort_values(by='Signal Time', ascending=False)
                st.dataframe(sorted_df, use_container_width=True)
            else:
                st.info("Analysis complete. No stocks are currently showing a 'Buy' signal.")

    # --- Tab 2: Individual Stock Search ---
    with tab2:
        st.header("Deep-Dive on a Single Stock")
        
        omxs30_tickers = get_omxs30_tickers()
        # A single selectbox that also allows custom user input
        ticker_to_analyze = st.selectbox(
            "Select from OMXS30 or type any ticker:",
            options=[""] + omxs30_tickers,
            help="You can select from the list or start typing a custom ticker like 'GOOGL' or 'TSLA'."
        )

        if ticker_to_analyze:
            try:
                with st.spinner(f"Fetching and analyzing {ticker_to_analyze}..."):
                    stock_data = fetch(ticker_to_analyze)
                
                if not stock_data.empty:
                    strategy_data = generate_signals(stock_data)
                    
                    # --- Layout with Columns: Metrics on the left, Chart on the right ---
                    col1, col2 = st.columns([1, 3]) # Column 2 is 3x wider than Column 1

                    with col1:
                        st.subheader("Key Metrics")
                        last_price = strategy_data['Close'].iloc[-1]
                        sma_short = strategy_data['SMA_Short'].iloc[-1]
                        sma_long = strategy_data['SMA_Long'].iloc[-1]
                        
                        st.metric("Last Price", f"{last_price:.2f} SEK")
                        st.metric("Short SMA (10)", f"{sma_short:.2f}", f"{sma_short - last_price:.2f}")
                        st.metric("Long SMA (50)", f"{sma_long:.2f}", f"{sma_long - last_price:.2f}")

                    with col2:
                        fig = plot_stock_chart(strategy_data, ticker_to_analyze)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Hide the large dataframe in an expander
                    with st.expander("View Full Data and Signals"):
                        st.dataframe(strategy_data)
                else:
                    st.warning("No data found for this ticker.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    run_app()
