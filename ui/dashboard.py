import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.fetchers.yahoo_fetcher import fetch
from strategies.moving_average import generate_signals

# (get_omxs30_tickers and plot_stock_chart functions remain the same as before)
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

    # --- Initialize portfolio in session state if it doesn't exist ---
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []

    # --- Tabs for different functionalities ---
    tab1, tab2, tab3 = st.tabs(["📈 OMXS30 Screener", "🔍 Individual Stock Analysis", "💼 My Portfolio"])

    # --- Tab 1 & 2 (remain the same as before) ---
    with tab1:
        # (Code for Tab 1 is unchanged)
        st.header("Find Recent Buy Signals")
        if st.button("Analyze All OMXS30 Stocks", type="primary"):
            tickers = get_omxs30_tickers()
            buy_recommendations = []
            progress_bar = st.progress(0, text="Starting analysis...")
            
            for i, ticker in enumerate(tickers):
                try:
                    data = fetch(ticker)
                    if not data.empty:
                        strategy_data = generate_signals(data)
                        last_position = strategy_data['Position'].iloc[-1]
                        if last_position == 2:
                            buy_recommendations.append({
                                'Ticker': ticker, 'Last Price': f"{strategy_data['Close'].iloc[-1]:.2f}",
                                'Signal Time': strategy_data.index[strategy_data['Position'] == 2][-1].strftime('%Y-%m-%d %H:%M')
                            })
                except Exception: continue
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

    with tab2:
        # (Code for Tab 2 is unchanged)
        st.header("Deep-Dive on a Single Stock")
        omxs30_tickers = get_omxs30_tickers()
        ticker_to_analyze = st.selectbox("Select from OMXS30 or type any ticker:", options=[""] + omxs30_tickers, help="You can select from the list or start typing a custom ticker like 'GOOGL' or 'TSLA'.")

        if ticker_to_analyze:
            try:
                with st.spinner(f"Fetching and analyzing {ticker_to_analyze}..."):
                    stock_data = fetch(ticker_to_analyze)
                if not stock_data.empty:
                    strategy_data = generate_signals(stock_data)
                    col1, col2 = st.columns([1, 3])
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
                    with st.expander("View Full Data and Signals"):
                        st.dataframe(strategy_data)
                else:
                    st.warning("No data found for this ticker.")
            except Exception as e: st.error(f"An error occurred: {e}")

    # --- Tab 3: My Portfolio ---
    with tab3:
        st.header("My Portfolio Tracker")

        # --- Input Form to Add Holdings ---
        with st.form("add_holding_form", clear_on_submit=True):
            st.write("Add a new stock to your portfolio")
            col1, col2, col3 = st.columns(3)
            ticker = col1.text_input("Ticker Symbol").upper()
            quantity = col2.number_input("Quantity", min_value=0.01, step=0.01, format="%.2f")
            gav = col3.number_input("Average Cost (GAV)", min_value=0.01, step=0.01, format="%.2f")
            
            submitted = st.form_submit_button("Add to Portfolio")
            if submitted and ticker and quantity > 0 and gav > 0:
                st.session_state.portfolio.append({"ticker": ticker, "quantity": quantity, "gav": gav})
                st.success(f"Added {quantity} shares of {ticker} to your portfolio!")

        st.write("---")

        # --- Display Portfolio ---
        if not st.session_state.portfolio:
            st.info("Your portfolio is empty. Add a stock using the form above.")
        else:
            portfolio_data = []
            total_value = 0
            total_investment = 0
            
            with st.spinner("Updating portfolio data..."):
                for holding in st.session_state.portfolio:
                    try:
                        data = fetch(holding["ticker"])
                        if data.empty: continue
                        
                        strategy_data = generate_signals(data)
                        current_price = data['Close'].iloc[-1]
                        investment_value = holding["quantity"] * holding["gav"]
                        current_value = holding["quantity"] * current_price
                        profit_loss = current_value - investment_value
                        profit_loss_pct = (profit_loss / investment_value) * 100 if investment_value != 0 else 0
                        
                        # Get the latest signal from the strategy
                        last_signal_val = strategy_data['Signal'].iloc[-1]
                        suggestion = "Hold" if last_signal_val == 1 else "Sell"

                        portfolio_data.append({
                            "Ticker": holding["ticker"], "Quantity": holding["quantity"], "GAV": f"{holding['gav']:.2f}",
                            "Current Price": f"{current_price:.2f}", "Current Value": f"{current_value:.2f}",
                            "P/L": f"{profit_loss:.2f}", "P/L %": f"{profit_loss_pct:.2f}%",
                            "Suggestion": suggestion
                        })
                        
                        total_value += current_value
                        total_investment += investment_value
                    except Exception:
                        continue
            
            if portfolio_data:
                # --- Display Portfolio Summary ---
                total_pl = total_value - total_investment
                total_pl_pct = (total_pl / total_investment) * 100 if total_investment != 0 else 0
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Portfolio Value", f"{total_value:,.2f} SEK")
                col2.metric("Total Profit/Loss", f"{total_pl:,.2f} SEK")
                col3.metric("Total P/L %", f"{total_pl_pct:.2f}%", delta=f"{total_pl_pct:.2f}%")

                st.write("---")
                
                # --- Display Portfolio Table with Styling ---
                portfolio_df = pd.DataFrame(portfolio_data)
                
                def style_table(df):
                    def color_pl(val):
                        if isinstance(val, str) and '%' in val: val = float(val.replace('%', ''))
                        elif isinstance(val, str): val = float(val)
                        color = 'green' if val > 0 else 'red' if val < 0 else 'white'
                        return f'color: {color}'
                    
                    def color_suggestion(val):
                        color = 'green' if val == 'Hold' else 'red'
                        return f'color: {color}; font-weight: bold'

                    return df.style.applymap(color_pl, subset=['P/L', 'P/L %'])\
                                     .applymap(color_suggestion, subset=['Suggestion'])

                st.dataframe(style_table(portfolio_df), use_container_width=True)

if __name__ == "__main__":
    run_app()
