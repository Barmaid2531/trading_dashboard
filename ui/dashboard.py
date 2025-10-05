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
    """Returns a dictionary of major Nordic indices and their component tickers."""
    indices = {
        "OMXS30 (Sweden)": ['ERIC-B.ST', 'ADDT-B.ST', 'SCA-B.ST', 'AZN.ST', 'BOL.ST', 'SAAB-B.ST', 'NDA-SE.ST', 'SKA-B.ST','TEL2-B.ST', 'HM-B.ST', 'TELIA.ST', 'NIBE-B.ST', 'LIFCO-B.ST', 'SHB-A.ST', 'SEB-A.ST', 'ESSITY-B.ST','SWED-A.ST', 'EVO.ST', 'SKF-B.ST', 'INDU-C.ST', 'SAND.ST', 'VOLV-B.ST', 'HEXA-B.ST', 'ABB.ST','ASSA-B.ST', 'EPI-A.ST', 'INVE-B.ST', 'EQT.ST', 'ALFA.ST', 'ATCO-A.ST'],
        "OMXC25 (Denmark)": ['MAERSK-B.CO', 'NOVO-B.CO', 'DSV.CO', 'VWS.CO', 'PNDORA.CO', 'GN.CO', 'ORSTED.CO', 'DANSKE.CO','NZYM-B.CO', 'GMAB.CO', 'TRYG.CO', 'CARL-B.CO', 'COLOB.CO', 'CHR.CO', 'JYSK.CO', 'RBREW.CO','ROCK-B.CO', 'ISS.CO', 'DEMANT.CO', 'AMBU-B.CO', 'BAVA.CO', 'NETC.CO', 'NDA-DK.CO', 'SYDB.CO', 'FLS.CO'],
        "OMXH25 (Finland)": ['NOKIA.HE', 'SAMPO.HE', 'KNEBV.HE', 'FORTUM.HE', 'UPM.HE', 'NESTE.HE', 'STERV.HE', 'ELISA.HE','WRT1V.HE', 'OUT1V.HE', 'TIETO.HE', 'ORNBV.HE', 'HUH1V.HE', 'CGCBV.HE', 'KESKOB.HE', 'MOCORP.HE','VALMT.HE', 'YIT.HE', 'KCR.HE', 'TELIA1.HE', 'NDA-FI.HE', 'SSABBH.HE', 'METSO.HE', 'QTCOM.HE', 'KOJAMO.HE'],
        "OBX (Norway)": ['EQNR.OL', 'DNB.OL', 'TEL.OL', 'MOWI.OL', 'AKERBP.OL', 'YAR.OL', 'NHY.OL', 'ORK.OL','SUBC.OL', 'SALM.OL', 'AKSO.OL', 'SCHA.OL', 'NEL.OL', 'FRO.OL', 'STB.OL', 'NOD.OL', 'GJF.OL', 'RECSI.OL', 'BWO.OL', 'NAS.OL', 'OTL.OL', 'SCATC.OL', 'TGS.OL']
    }
    return indices

def plot_stock_chart(strategy_data, ticker_symbol):
    if strategy_data is None or len(strategy_data) < 2:
        fig = go.Figure()
        fig.update_layout(title=f'{ticker_symbol} - Not Enough Data', xaxis_visible=False, yaxis_visible=False)
        return fig
    
    start_price, end_price = strategy_data['Close'].iloc[0], strategy_data['Close'].iloc[-1]
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
    try:
        with st.spinner(f"Fetching data for {ticker}..."):
            stock_data = fetch_daily_bars(ticker)
        
        if stock_data.empty:
            st.warning("No data found for this ticker.")
            return

        strategy_data = analyze_stock(stock_data, ticker)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.subheader("Key Metrics")
            last_row = strategy_data.iloc[-1]
            st.metric("Last Price", f"{last_row['Close']:.2f}")
            st.metric("RSI (14)", f"{last_row['RSI_14']:.2f}")
            st.metric("Signal Score", f"{int(last_row['Signal_Score'])}/5")
            st.info(f"Recommendation: **{last_row['Recommendation']}**")
            
            st.write("---")
            st.subheader("Risk Levels")
            st.metric("Stop-Loss", f"{last_row['Stop_Loss']:.2f}", f"-{last_row['Close'] - last_row['Stop_Loss']:.2f} (Risk)", delta_color="inverse")
            st.metric("Take-Profit", f"{last_row['Take_Profit']:.2f}", f"+{last_row['Take_Profit'] - last_row['Close']:.2f} (Reward)", delta_color="normal")
            st.caption("Based on a 2:1 Reward/Risk ratio using ATR.")

        with col2:
            fig = plot_stock_chart(strategy_data, ticker)
            st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("View Full Data and Signals"):
            st.dataframe(strategy_data)
    except Exception as e:
        st.error(f"An error occurred while analyzing {ticker}."), st.exception(e)

def calculate_portfolio_summary(portfolio):
    """Helper function to calculate portfolio totals."""
    total_value, total_investment = 0, 0
    if not portfolio:
        return 0, 0, 0, 0
    for holding in portfolio:
        try:
            data = fetch_daily_bars(holding["ticker"], period="5d")
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                total_investment += holding["quantity"] * holding["gav"]
                total_value += holding["quantity"] * current_price
        except Exception:
            continue
    total_pl = total_value - total_investment
    total_pl_pct = (total_pl / total_investment) * 100 if total_investment != 0 else 0
    return total_value, total_investment, total_pl, total_pl_pct

def run_app():
    st.set_page_config(page_title="Trading Dashboard", layout="wide")

    if 'portfolio' not in st.session_state: st.session_state.portfolio = []
    if 'watchlist' not in st.session_state: st.session_state.watchlist = []
    if 'screener_view_ticker' not in st.session_state: st.session_state.screener_view_ticker = None

    with st.sidebar:
        st.title("💹 Trading Dashboard")
        st.info("Swing trading analysis for Nordic markets."), st.write("---")
        st.header("My Data")
        uploaded_file = st.file_uploader("Import Data (JSON)", type=['json'])
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                st.session_state.portfolio = data.get('portfolio', [])
                st.session_state.watchlist = data.get('watchlist', [])
                st.success("Data imported!"), st.rerun()
            except Exception as e: st.error(f"Error importing file: {e}")
        if st.session_state.portfolio or st.session_state.watchlist:
            data_to_export = {"portfolio": st.session_state.portfolio, "watchlist": st.session_state.watchlist}
            st.download_button("Export Data", json.dumps(data_to_export, indent=4), "my_data.json", "application/json")
        st.write("---"), st.warning("Disclaimer: Not financial advice.")

    st.title("Nordic Market Swing Trading Analysis")

    tabs = st.tabs(["🏠 Dashboard", "📈 Screener", "🔍 Individual Analysis", "💼 Portfolio", "🔭 Watchlist", "🧪 Backtester"])

    with tabs[0]:
        st.header("At-a-Glance Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Portfolio Snapshot")
            total_value, _, _, total_pl_pct = calculate_portfolio_summary(st.session_state.portfolio)
            c1, c2 = st.columns(2)
            c1.metric("Total Value", f"{total_value:,.2f} SEK")
            c2.metric("Total P/L %", f"{total_pl_pct:.2f}%")
        with col2:
            st.subheader("Market Snapshot")
            if 'recommendations' in st.session_state and not st.session_state.recommendations.empty:
                st.metric("Strong Buy Signals Found", len(st.session_state.recommendations))
            else:
                st.metric("Strong Buy Signals Found", "N/A", help="Run a scan in the 'Screener' tab.")
        
        st.write("---")
        st.subheader("Market Context: OMXS30")
        omx_data = fetch_daily_bars("^OMX", period="6mo")
        if not omx_data.empty:
            st.line_chart(omx_data['Close'])

    with tabs[1]:
        st.header("Nordic Index Screener")
        if st.session_state.screener_view_ticker:
            st.subheader(f"Analysis for {st.session_state.screener_view_ticker}")
            display_detailed_view(st.session_state.screener_view_ticker)
            if st.button("⬅️ Back to Screener Results"):
                st.session_state.screener_view_ticker = None; st.rerun()
        else:
            nordic_indices = get_nordic_indices()
            selected_index = st.selectbox("Select an Index to Scan:", options=list(nordic_indices.keys()))
            if st.button(f"Scan {selected_index} for Strong Buy Signals", type="primary"):
                tickers_to_scan = nordic_indices[selected_index]
                strong_buys = []
                progress_bar = st.progress(0)
                for i, ticker in enumerate(tickers_to_scan):
                    progress_bar.progress((i + 1) / len(tickers_to_scan), f"Scanning {ticker}...")
                    try:
                        data = fetch_daily_bars(ticker, period="1y")
                        if not data.empty and len(data) > 50:
                            strategy_data = analyze_stock(data, ticker)
                            last_row = strategy_data.iloc[-1]
                            if last_row['Signal_Score'] >= 4:
                                strong_buys.append({
                                    'Ticker': ticker, 'Last Price': f"{last_row['Close']:.2f}",
                                    'Signal Score': f"{int(last_row['Signal_Score'])}/5", 'Recommendation': last_row['Recommendation']
                                })
                    except Exception: continue
                progress_bar.empty()
                st.session_state.recommendations = pd.DataFrame(strong_buys)

            if 'recommendations' in st.session_state:
                df = st.session_state.recommendations
                st.metric("Strong Buy Signals Found", len(df))
                st.write("---")
                if not df.empty:
                    for _, row in df.iterrows():
                        with st.container(border=True):
                            c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
                            c1.subheader(row['Ticker'])
                            c2.metric("Last Price", row['Last Price'])
                            c3.metric("Signal Score", row['Signal Score'])
                            if c4.button("Analyze", key=row['Ticker']):
                                st.session_state.screener_view_ticker = row['Ticker']; st.rerun()
                else:
                    st.info("No stocks in this index currently meet the 'Strong Buy' criteria.")

    with tabs[2]:
        st.header("Deep-Dive on a Single Stock")
        custom_ticker = st.text_input("Enter Any Ticker", key="custom_ticker").upper()
        if custom_ticker:
            display_detailed_view(custom_ticker)

    with tabs[3]:
        st.header("My Portfolio Tracker")
        with st.form("add_holding_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            ticker, qty, gav = c1.text_input("Ticker").upper(), c2.number_input("Quantity", 0.01, format="%.2f"), c3.number_input("GAV", 0.01, format="%.2f")
            if st.form_submit_button("Add to Portfolio"):
                if ticker and qty > 0 and gav > 0:
                    st.session_state.portfolio.append({"ticker": ticker, "quantity": qty, "gav": gav}); st.success(f"Added {ticker}!")
        
        if st.session_state.portfolio:
            portfolio_data, total_value, total_investment = [], 0, 0
            with st.spinner("Updating portfolio..."):
                for holding in st.session_state.portfolio:
                    try:
                        data = fetch_daily_bars(holding["ticker"])
                        if data.empty: continue
                        strategy_data = analyze_stock(data, holding["ticker"])
                        last_row = strategy_data.iloc[-1]
                        current_price, investment_value = last_row['Close'], holding["quantity"] * holding["gav"]
                        current_value = holding["quantity"] * current_price
                        profit_loss, profit_loss_pct = current_value - investment_value, (current_value / investment_value - 1) * 100 if investment_value != 0 else 0
                        portfolio_data.append({
                            "Ticker": holding["ticker"], "Quantity": holding["quantity"], "GAV": f"{holding['gav']:.2f}",
                            "Current Price": f"{current_price:.2f}", "Current Value": f"{current_value:.2f}",
                            "P/L": f"{profit_loss:.2f}", "P/L %": f"{profit_loss_pct:.2f}%", "Suggestion": last_row['Recommendation']
                        })
                        total_value, total_investment = total_value + current_value, total_investment + investment_value
                    except Exception: continue
            
            if portfolio_data:
                total_pl = total_value - total_investment
                total_pl_pct = (total_pl / total_investment) * 100 if total_investment != 0 else 0
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Value", f"{total_value:,.2f} SEK"), c2.metric("Total P/L", f"{total_pl:,.2f} SEK"), c3.metric("Total P/L %", f"{total_pl_pct:.2f}%")
                st.write("---")
                def style_table(df):
                    def color(val, sugg=False):
                        if sugg: return f'color: {"green" if "Buy" in str(val) else "red" if "Sell" in str(val) else "white"}'
                        try:
                            num = float(str(val).replace('%',''))
                            return f'color: {"green" if num > 0 else "red" if num < 0 else "white"}'
                        except (ValueError, TypeError): return ''
                    return df.style.applymap(lambda v: color(v, sugg=True), subset=['Suggestion']).applymap(lambda v: color(v, sugg=False), subset=['P/L', 'P/L %'])
                st.dataframe(style_table(pd.DataFrame(portfolio_data)), use_container_width=True)

                st.write("---")
                st.subheader("Manage & Analyze Portfolio")
                portfolio_tickers = [h['ticker'] for h in st.session_state.portfolio]
                selected_ticker = st.selectbox("Select a holding:", [""] + portfolio_tickers, key="portfolio_select")
                if selected_ticker:
                    display_detailed_view(selected_ticker)
                    st.write("---"), st.write(f"Editing **{selected_ticker}**")
                    idx = portfolio_tickers.index(selected_ticker)
                    holding_to_edit = st.session_state.portfolio[idx]
                    c1, c2 = st.columns(2)
                    new_qty = c1.number_input("New Qty", value=holding_to_edit['quantity'], key=f"qty_{selected_ticker}")
                    new_gav = c2.number_input("New GAV", value=holding_to_edit['gav'], key=f"gav_{selected_ticker}")
                    c1, c2 = st.columns([1, 1])
                    if c1.button("Update", key=f"up_{selected_ticker}"):
                        st.session_state.portfolio[idx] = {"ticker": selected_ticker, "quantity": new_qty, "gav": new_gav}; st.success(f"Updated {selected_ticker}!"); st.rerun()
                    if c2.button("Delete", key=f"del_{selected_ticker}"):
                        st.session_state.portfolio.pop(idx); st.warning(f"Deleted {selected_ticker}."); st.rerun()

    with tabs[4]:
        st.header("My Stock Watchlist")
        with st.form("add_watchlist_form", clear_on_submit=True):
            ticker_to_watch = st.text_input("Enter Ticker Symbol").upper()
            if st.form_submit_button("Add to Watchlist"):
                if ticker_to_watch and ticker_to_watch not in st.session_state.watchlist:
                    st.session_state.watchlist.append(ticker_to_watch); st.success(f"Added {ticker_to_watch}!")
                else: st.warning(f"{ticker_to_watch} is invalid or already on the list.")
        
        if st.session_state.watchlist:
            watchlist_data = []
            with st.spinner("Updating watchlist..."):
                for ticker in st.session_state.watchlist:
                    try:
                        data = fetch_daily_bars(ticker, period="1y")
                        if data.empty: continue
                        strategy_data = analyze_stock(data, ticker)
                        last_row = strategy_data.iloc[-1]
                        watchlist_data.append({
                            "Ticker": ticker, "Current Price": f"{last_row['Close']:.2f}",
                            "RSI": f"{last_row['RSI_14']:.2f}", "Signal Score": f"{int(last_row['Signal_Score'])}/5",
                            "Recommendation": last_row['Recommendation']
                        })
                    except Exception: continue
            if watchlist_data:
                def style_watchlist(df):
                    def color_signal(val): return f'color: {"green" if "Buy" in str(val) else "red" if "Sell" in str(val) else "white"}'
                    return df.style.applymap(color_signal, subset=['Recommendation'])
                st.dataframe(style_watchlist(pd.DataFrame(watchlist_data)), use_container_width=True)
            
            st.write("---")
            st.subheader("Analyze or Manage Watchlist")
            selected_ticker_wl = st.selectbox("Select a stock:", [""] + st.session_state.watchlist, key="watchlist_select")
            if selected_ticker_wl:
                display_detailed_view(selected_ticker_wl)
                if st.button("Remove from Watchlist"):
                    st.session_state.watchlist.remove(selected_ticker_wl); st.warning(f"Removed {selected_ticker_wl}."); st.rerun()

    with tabs[5]:
        st.header("Strategy Backtester")
        with st.form("backtest_form"):
            c1, c2, c3 = st.columns(3)
            ticker, start_date, end_date = c1.text_input("Ticker", "AAPL").upper(), c2.date_input("Start Date", pd.to_datetime("2023-01-01")), c3.date_input("End Date", pd.to_datetime("2024-01-01"))
            if st.form_submit_button("Run Backtest"):
                with st.spinner(f"Running backtest..."):
                    try:
                        stats, script, div = run_backtest(ticker, start_date, end_date)
                        if stats is not None:
                            st.success("Backtest complete!")
                            st.subheader("Key Performance Metrics")
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Return [%]", f"{stats['Return [%]']:.2f}%"), c2.metric("Win Rate [%]", f"{stats['Win Rate [%]']:.2f}%"),
                            c3.metric("Profit Factor", f"{stats['Profit Factor']:.2f}"), c4.metric("Max Drawdown [%]", f"{stats['Max. Drawdown [%]']:.2f}%")
                            st.subheader("Equity Curve & Trades")
                            if script and div: components.html(script + div, height=800, scrolling=True)
                            else: st.warning("No plot generated (no trades made).")
                            with st.expander("View Full Statistics Table"): st.write(stats)
                        else: st.error("Could not fetch data.")
                    except ValueError as e: st.error(e)

if __name__ == "__main__":
    run_app()
