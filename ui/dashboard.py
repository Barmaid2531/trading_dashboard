import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Import our new strategy function
from strategies.moving_average import generate_signals
from data.fetchers.yahoo_fetcher import fetch

def run_app():
    st.set_page_config(page_title="Trading Dashboard", page_icon="💹", layout="wide")
    st.title("Intraday Trading Strategy Dashboard")

    st.sidebar.header("User Input")
    ticker_symbol = st.sidebar.text_input("Enter Stock Ticker", "NVDA").upper()

    if ticker_symbol:
        st.header(f"Moving Average Crossover Strategy for: {ticker_symbol}")

        try:
            with st.spinner(f"Fetching intraday data for {ticker_symbol}..."):
                stock_data = fetch(ticker_symbol)

            if not stock_data.empty:
                # --- Generate Signals ---
                strategy_data = generate_signals(stock_data)

                # --- Create the Plot ---
                fig = go.Figure()

                # 1. Plot Closing Price
                fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['Close'], 
                                         name='Close Price', line=dict(color='skyblue')))

                # 2. Plot Moving Averages
                fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_Short'], 
                                         name='Short SMA', line=dict(color='orange')))
                fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_Long'], 
                                         name='Long SMA', line=dict(color='purple')))

                # 3. Plot Buy Signals (where Position changes to 1)
                buy_signals = strategy_data[strategy_data['Position'] == 2]
                fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['SMA_Short'], 
                                         name='Buy Signal', mode='markers', 
                                         marker=dict(symbol='triangle-up', color='green', size=12)))
                                         
                # 4. Plot Sell Signals (where Position changes to -1)
                sell_signals = strategy_data[strategy_data['Position'] == -2]
                fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['SMA_Short'], 
                                         name='Sell Signal', mode='markers', 
                                         marker=dict(symbol='triangle-down', color='red', size=12)))

                fig.update_layout(title=f'{ticker_symbol} Trading Signals',
                                  xaxis_title='Date',
                                  yaxis_title='Price',
                                  legend_title='Legend')
                
                st.plotly_chart(fig, use_container_width=True)

                # --- Display Data ---
                st.subheader("Data with Strategy Signals")
                st.dataframe(strategy_data)
            else:
                st.warning("No intraday data returned. The ticker may be invalid or delisted.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.info("Please enter a stock ticker to begin.")

if __name__ == "__main__":
    run_app()
