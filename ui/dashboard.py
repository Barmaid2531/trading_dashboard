import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
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

    # --- Initialize session state ---
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []

    # --- Sidebar ---
    with st.sidebar:
        st.title("💹 Trading Dashboard")
        st.info("An educational tool to analyze stocks using a Moving Average Crossover strategy.")
        st.write("---")
        
        # --- Portfolio Import/Export ---
        st.header("My Portfolio Data")
        
        uploaded_file = st.file_uploader("Import Portfolio", type=['json'])
        if uploaded_file is not None:
            try:
                portfolio_data = json.load(uploaded_file)
                st.session_state.portfolio = portfolio_data
                st.success("Portfolio imported successfully!")
            except Exception as e:
                st.error(f"Error importing file: {e}")

        if st.session_state.portfolio:
            portfolio_json = json.dumps(st.session_state.portfolio, indent=4)
            st.download_button(
                label="Export Portfolio",
                data=portfolio_json,
                file_name="my_portfolio.json",
                mime="application/json"
            )
        
        st.write("---")
        st.warning("Disclaimer: Not financial advice. Use at your own risk.")

    # --- Main Page Title ---
    st.title("Intraday Stock Analysis")

    # --- Tabs for different functionalities ---
    tab1, tab2, tab3, tab4 = st.tabs(["📈 OMXS30 Screener", "🔍 Individual Analysis", "💼 My Portfolio", "🔭 Watchlist"])

    with tab1:
        st.header("Find Recent Buy Signals (OMXS30)")
        if st.button("Analyze All OMXS30 Stocks", type="primary"):
            tickers = get_omxs30_tickers()
            buy_recommendations = []
            progress_bar = st.progress(0, text="Starting analysis...")
            for i, ticker in enumerate(tickers):
                progress_text = f"Analyzing {ticker} ({i+1}/{len(tickers)})..."
                progress_bar.progress((i + 1) / len(tickers), text=progress_text)
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

    with tab3:
        st.header("My Portfolio Tracker")
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
        if not st.session_state.portfolio:
            st.info("Your portfolio is empty. Add a stock or import a portfolio file from the sidebar.")
        else:
            portfolio_data, total_value, total_investment = [], 0, 0
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
                        last_signal_val = strategy_data['Signal'].iloc[-1]
                        suggestion = "Hold" if last_signal_val == 1 else "Sell"
                        portfolio_data.append({
                            "Ticker": holding["ticker"], "Quantity": holding["quantity"], "GAV": f"{holding['gav']:.2f}",
                            "Current Price": f"{current_price:.2f}", "Current Value": f"{current_value:.2f}",
                            "P/L": f"{profit_loss:.2f}", "P/L %": f"{profit_loss_pct:.2f}%", "Suggestion": suggestion
                        })
                        total_value += current_value
                        total_investment += investment_value
                    except Exception: continue
            if portfolio_data:
                total_pl = total_value - total_investment
                total_pl_pct = (total_pl / total_investment) * 100 if total_investment != 0 else 0
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Portfolio Value", f"{total_value:,.2f} SEK")
                col2.metric("Total Profit/Loss", f"{total_pl:,.2f} SEK")
                col3.metric("Total P/L %", f"{total_pl_pct:.2f}%")
                st.write("---")
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
                    return df.style.applymap(color_pl, subset=['P/L', 'P/L %']).applymap(color_suggestion, subset=['Suggestion'])
                st.dataframe(style_table(portfolio_df), use_container_width=True)
                st.write("---")
                st.subheader("Manage Portfolio")
                tickers_in_portfolio = [h['ticker'] for h in st.session_state.portfolio]
                selected_ticker_to_manage = st.selectbox("Select a holding to manage:", options=[""] + tickers_in_portfolio)
                if selected_ticker_to_manage:
                    selected_index = tickers_in_portfolio.index(selected_ticker_to_manage)
                    holding_to_edit = st.session_state.portfolio[selected_index]
                    st.write(f"Editing **{selected_ticker_to_manage}**")
                    col1, col2 = st.columns(2)
                    new_quantity = col1.number_input("New Quantity", value=holding_to_edit['quantity'], min_value=0.0, step=0.01, format="%.2f", key=f"qty_{selected_ticker_to_manage}")
                    new_gav = col2.number_input("New GAV", value=holding_to_edit['gav'], min_value=0.0, step=0.01, format="%.2f", key=f"gav_{selected_ticker_to_manage}")
                    col1, col2 = st.columns([1, 1])
                    if col1.button("Update Holding", key=f"update_{selected_ticker_to_manage}"):
                        st.session_state.portfolio[selected_index] = {"ticker": selected_ticker_to_manage, "quantity": new_quantity, "gav": new_gav}
                        st.success(f"Updated {selected_ticker_to_manage}!")
                        st.rerun()
                    if col2.button("❌ Delete Holding", key=f"delete_{selected_ticker_to_manage}"):
                        st.session_state.portfolio.pop(selected_index)
                        st.warning(f"Deleted {selected_ticker_to_manage} from portfolio.")
                        st.rerun()

    with tab4:
        st.header("My Stock Watchlist")
        with st.form("add_watchlist_form", clear_on_submit=True):
            ticker_to_watch = st.text_input("Enter Ticker Symbol to Watch").upper()
            submitted = st.form_submit_button("Add to Watchlist")
            if submitted and ticker_to_watch:
                if ticker_to_watch not in st.session_state.watchlist:
                    st.session_state.watchlist.append(ticker_to_watch)
                    st.success(f"Added {ticker_to_watch} to your watchlist!")
                else:
                    st.warning(f"{ticker_to_watch} is already in your watchlist.")
        st.write("---")
        if not st.session_state.watchlist:
            st.info("Your watchlist is empty. Add a stock using the form above.")
        else:
            watchlist_data = []
            with st.spinner("Updating watchlist..."):
                for ticker in st.session_state.watchlist:
                    try:
                        data = fetch(ticker)
                        if data.empty: continue
                        strategy_data = generate_signals(data)
                        current_price = strategy_data['Close'].iloc[-1]
                        signal_val = strategy_data['Signal'].iloc[-1]
                        signal = "Buy" if signal_val == 1 else "Sell"
                        watchlist_data.append({
                            "Ticker": ticker, "Current Price": f"{current_price:.2f}",
                            "SMA Short (10)": f"{strategy_data['SMA_Short'].iloc[-1]:.2f}",
                            "SMA Long (50)": f"{strategy_data['SMA_Long'].iloc[-1]:.2f}", "Signal": signal
                        })
                    except Exception: continue
            if watchlist_data:
                watchlist_df = pd.DataFrame(watchlist_data)
                def style_watchlist(df):
                    def color_signal(val):
                        color = 'green' if val == 'Buy' else 'red'
                        return f'color: {color}; font-weight: bold'
                    return df.style.applymap(color_signal, subset=['Signal'])
                st.dataframe(style_watchlist(watchlist_df), use_container_width=True)
            st.write("---")
            st.subheader("Manage Watchlist")
            ticker_to_remove = st.selectbox("Select a stock to remove:", options=[""] + st.session_state.watchlist)
            if st.button("Remove from Watchlist") and ticker_to_remove:
                st.session_state.watchlist.remove(ticker_to_remove)
                st.warning(f"Removed {ticker_to_remove} from your watchlist.")
                st.rerun()
