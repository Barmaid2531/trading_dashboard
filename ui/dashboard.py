import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots # <-- 1. ADD THIS NEW IMPORT
import json
from data.fetchers.yahoo_fetcher import fetch
from strategies.advanced_analyzer import analyze_stock
from strategies.backtest import run_backtest
from bokeh.plotting import figure # Add Bokeh for plotting

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
    """
    Generates a high-resolution Plotly figure with a range slider 
    and percentage change calculation.
    """
    if strategy_data is None or len(strategy_data) < 2:
        fig = go.Figure()
        fig.update_layout(title=f'{ticker_symbol} - Not Enough Data to Display Chart', xaxis_visible=False, yaxis_visible=False,
                          annotations=[dict(text="No recent intraday data available.", xref="paper", yref="paper", showarrow=False, font=dict(size=16))])
        return fig

    start_price = strategy_data['Close'].iloc[0]
    end_price = strategy_data['Close'].iloc[-1]
    percent_change = ((end_price / start_price) - 1) * 100 if start_price != 0 else 0
    change_color = "green" if percent_change >= 0 else "red"
    chart_title = f"{ticker_symbol} Advanced Analysis | Period Change: <span style='color:{change_color};'>{percent_change:.2f}%</span>"

    # --- 2. THE FIX: Use make_subplots() instead of go.Figure() ---
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, 
                        row_heights=[0.6, 0.2, 0.2])

    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['Close'], name='Close Price', line=dict(color='skyblue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_10'], name='Short SMA', line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_50'], name='Long SMA', line=dict(color='purple')), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['MACD_12_26_9'], name='MACD', line=dict(color='blue')), row=2, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['MACDs_12_26_9'], name='Signal Line', line=dict(color='red')), row=2, col=1)
    fig.add_trace(go.Bar(x=strategy_data.index, y=strategy_data['MACDh_12_26_9'], name='Histogram', marker_color='grey'), row=2, col=1)

    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['RSI_14'], name='RSI', line=dict(color='green')), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="blue", row=3, col=1)

    fig.update_layout(title_text=chart_title, height=800, legend_title='Legend', showlegend=True)
    fig.update_yaxes(title_text="Price (SEK)", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    
    fig.update_xaxes(rangeslider_visible=True, row=1, col=1)
    return fig

def display_detailed_view(ticker):
    """Fetches, analyzes, and displays the detailed view for a single stock."""
    try:
        with st.spinner(f"Fetching and analyzing {ticker}..."):
            stock_data = fetch(ticker)
        
        if stock_data.empty:
            st.warning("No data found for this ticker.")
            return

        strategy_data = analyze_stock(stock_data)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.subheader("Key Metrics")
            last_row = strategy_data.iloc[-1]
            
            st.metric("Last Price", f"{last_row['Close']:.2f} SEK")
            st.metric("RSI (14)", f"{last_row['RSI_14']:.2f}")
            st.metric("MACD Hist", f"{last_row['MACDh_12_26_9']:.2f}")
            st.metric("Signal Score", f"{int(last_row['Signal_Score'])}/4", help="Based on SMA, MACD, RSI, and OBV indicators.")
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
    st.set_page_config(page_title="Trading Dashboard", page_icon="💹", layout="wide")

    if 'portfolio' not in st.session_state: st.session_state.portfolio = []
    if 'watchlist' not in st.session_state: st.session_state.watchlist = []

    with st.sidebar:
        st.title("💹 Trading Dashboard")
        st.info("An advanced tool to analyze stocks using multiple technical indicators.")
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
        st.warning("Disclaimer: Not financial advice. Use at your own risk.")

    st.title("Advanced Intraday Stock Analysis")

    tab1, tab2, tab3, tab4 = st.tabs(["📈 Screener", "🔍 Individual Analysis", "💼 Portfolio", "🔭 Watchlist","🧪 Backtester"])

    with tab1:
        st.header("Find Strong Buy Signals (OMXS30)")
        if st.button("Analyze All OMXS30 Stocks", type="primary"):
            tickers = get_omxs30_tickers()
            strong_buys = []
            progress_bar = st.progress(0, text="Starting analysis...")
            for i, ticker in enumerate(tickers):
                progress_bar.progress((i + 1) / len(tickers), f"Analyzing {ticker}...")
                try:
                    data = fetch(ticker)
                    if not data.empty and len(data) > 1:
                        strategy_data = analyze_stock(data)
                        last_row = strategy_data.iloc[-1]
                        if last_row['Signal_Score'] >= 3:
                            strong_buys.append({
                                'Ticker': ticker, 
                                'Last Price': f"{last_row['Close']:.2f}",
                                'Signal Score': f"{int(last_row['Signal_Score'])}/4",
                                'RSI': f"{last_row['RSI_14']:.2f}",
                                'Recommendation': last_row['Recommendation']
                            })
                except Exception: continue
            progress_bar.empty()
            st.session_state.recommendations = pd.DataFrame(strong_buys)

        if 'recommendations' in st.session_state:
            recommendations_df = st.session_state.recommendations
            st.metric("Strong Buy Signals Found", len(recommendations_df))
            if not recommendations_df.empty:
                st.success("Displaying stocks with the strongest buy signals.")
                st.dataframe(recommendations_df.sort_values(by='Signal Score', ascending=False), use_container_width=True)
            else:
                st.info("Analysis complete. No stocks currently meet the 'Strong Buy' criteria.")

    with tab2:
        st.header("Deep-Dive on a Single Stock")
        st.write("Select a stock from the OMXS30 list OR enter any other ticker below.")
        omxs30_tickers = get_omxs30_tickers()
        selected_ticker = st.selectbox("OMXS30 Stocks", [""] + omxs30_tickers)
        custom_ticker = st.text_input("Enter Custom Ticker (e.g., GOOGL, TSLA, BTC-USD)").upper()
        ticker_to_analyze = custom_ticker if custom_ticker else selected_ticker
        if ticker_to_analyze:
            display_detailed_view(ticker_to_analyze)

    with tab3:
        st.header("My Portfolio Tracker")
        with st.form("add_holding_form", clear_on_submit=True):
            st.write("Add a new stock to your portfolio")
            c1, c2, c3 = st.columns(3)
            ticker, quantity, gav = c1.text_input("Ticker").upper(), c2.number_input("Quantity", 0.01, step=0.01), c3.number_input("GAV", 0.01, step=0.01)
            if st.form_submit_button("Add to Portfolio"):
                if ticker and quantity > 0 and gav > 0:
                    st.session_state.portfolio.append({"ticker": ticker, "quantity": quantity, "gav": gav})
                    st.success(f"Added {ticker} to portfolio!")
        st.write("---")
        if not st.session_state.portfolio:
            st.info("Your portfolio is empty.")
        else:
            portfolio_data, total_value, total_investment = [], 0, 0
            with st.spinner("Updating portfolio..."):
                for holding in st.session_state.portfolio:
                    try:
                        data = fetch(holding["ticker"])
                        if data.empty: continue
                        strategy_data = analyze_stock(data)
                        last_row = strategy_data.iloc[-1]
                        current_price, investment_value = last_row['Close'], holding["quantity"] * holding["gav"]
                        current_value = holding["quantity"] * current_price
                        profit_loss, profit_loss_pct = current_value - investment_value, (current_value / investment_value - 1) * 100
                        portfolio_data.append({
                            "Ticker": holding["ticker"], "Quantity": holding["quantity"], "GAV": f"{holding['gav']:.2f}",
                            "Current Price": f"{current_price:.2f}", "Current Value": f"{current_value:.2f}",
                            "P/L": f"{profit_loss:.2f}", "P/L %": f"{profit_loss_pct:.2f}%", "Suggestion": last_row['Recommendation']
                        })
                        total_value, total_investment = total_value + current_value, total_investment + investment_value
                    except Exception: continue
            if portfolio_data:
                total_pl, total_pl_pct = total_value - total_investment, (total_value / total_investment - 1) * 100
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Value", f"{total_value:,.2f} SEK"), c2.metric("Total P/L", f"{total_pl:,.2f} SEK"), c3.metric("Total P/L %", f"{total_pl_pct:.2f}%")
                st.write("---")
                def style_table(df):
                    def color(val, sugg=False):
                        if sugg: return f'color: {"green" if "Buy" in val else "red" if "Sell" in val else "white"}'
                        num = float(str(val).replace('%',''))
                        return f'color: {"green" if num > 0 else "red" if num < 0 else "white"}'
                    return df.style.applymap(color, subset=['P/L', 'P/L %']).applymap(lambda v: color(v, sugg=True), subset=['Suggestion'])
                st.dataframe(style_table(pd.DataFrame(portfolio_data)), use_container_width=True)

                st.write("---")
                st.subheader("Manage & Analyze Portfolio")
                portfolio_tickers = [h['ticker'] for h in st.session_state.portfolio]
                selected_ticker = st.selectbox("Select a holding:", [""] + portfolio_tickers)
                if selected_ticker:
                    display_detailed_view(selected_ticker)
                    
                    st.write("---")
                    st.write(f"Editing **{selected_ticker}**")
                    idx = portfolio_tickers.index(selected_ticker)
                    holding_to_edit = st.session_state.portfolio[idx]
                    
                    c1, c2 = st.columns(2)
                    new_qty = c1.number_input("New Qty", value=holding_to_edit['quantity'], key=f"qty_{selected_ticker}")
                    new_gav = c2.number_input("New GAV", value=holding_to_edit['gav'], key=f"gav_{selected_ticker}")
                    c1, c2 = st.columns([1, 1])
                    if c1.button("Update", key=f"up_{selected_ticker}"):
                        st.session_state.portfolio[idx] = {"ticker": selected_ticker, "quantity": new_qty, "gav": new_gav}
                        st.success(f"Updated {selected_ticker}!"), st.rerun()
                    if c2.button("Delete", key=f"del_{selected_ticker}"):
                        st.session_state.portfolio.pop(idx)
                        st.warning(f"Deleted {selected_ticker}."), st.rerun()

    with tab4:
        st.header("My Stock Watchlist")
        with st.form("add_watchlist_form", clear_on_submit=True):
            ticker_to_watch = st.text_input("Enter Ticker Symbol").upper()
            if st.form_submit_button("Add to Watchlist"):
                if ticker_to_watch and ticker_to_watch not in st.session_state.watchlist:
                    st.session_state.watchlist.append(ticker_to_watch), st.success(f"Added {ticker_to_watch}!")
                else: st.warning(f"{ticker_to_watch} is invalid or already on the list.")
        st.write("---")
        if not st.session_state.watchlist:
            st.info("Your watchlist is empty.")
        else:
            watchlist_data = []
            with st.spinner("Updating watchlist..."):
                for ticker in st.session_state.watchlist:
                    try:
                        data = fetch(ticker)
                        if data.empty: continue
                        strategy_data = analyze_stock(data)
                        last_row = strategy_data.iloc[-1]
                        watchlist_data.append({
                            "Ticker": ticker, "Current Price": f"{last_row['Close']:.2f}",
                            "RSI": f"{last_row['RSI_14']:.2f}", "Signal Score": f"{int(last_row['Signal_Score'])}/4",
                            "Recommendation": last_row['Recommendation']
                        })
                    except Exception: continue
            if watchlist_data:
                def style_watchlist(df):
                    def color_signal(val): return f'color: {"green" if "Buy" in val else "red" if "Sell" in val else "white"}'
                    return df.style.applymap(color_signal, subset=['Recommendation'])
                st.dataframe(style_watchlist(pd.DataFrame(watchlist_data)), use_container_width=True)
            
            st.write("---")
            st.subheader("Analyze or Manage Watchlist")
            selected_ticker_wl = st.selectbox("Select a stock:", [""] + st.session_state.watchlist)
            if selected_ticker_wl:
                display_detailed_view(selected_ticker_wl)
                if st.button("Remove from Watchlist"):
                    st.session_state.watchlist.remove(selected_ticker_wl)
                    st.warning(f"Removed {selected_ticker_wl}."), st.rerun()
    with tab5:
        st.header("Strategy Backtester")
        st.info("Test the 'Strong Buy' (Signal Score >= 3) strategy on historical daily data.")
    
        with st.form("backtest_form"):
            col1, col2, col3 = st.columns(3)
            ticker = col1.text_input("Ticker Symbol", "AAPL").upper()
            start_date = col2.date_input("Start Date", pd.to_datetime("2022-01-01"))
            end_date = col3.date_input("End Date", pd.to_datetime("2023-01-01"))
            
            submitted = st.form_submit_button("Run Backtest")
    
        if submitted:
            with st.spinner(f"Running backtest for {ticker}..."):
                stats, plot = run_backtest(ticker, start_date, end_date)
            
            if stats is not None:
                st.success("Backtest complete!")
                
                st.subheader("Performance Metrics")
                st.write(stats) # Displays the main performance stats
                
                st.subheader("Equity Curve & Trades")
                st.bokeh_chart(plot, use_container_width=True)
                
                st.subheader("Full Stats")
                st.write(stats._strategy) # Displays more detailed stats
            else:
                st.error("Could not fetch data for the given ticker and date range.")

