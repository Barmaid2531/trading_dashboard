import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import streamlit.components.v1 as components
import yfinance as yf
import joblib

from data.fetchers.yfinance_fetcher import fetch_daily_bars, get_fx_rate
from strategies.advanced_analyzer import analyze_stock, analyze_stock_ml
from strategies.mean_reversion_analyzer import analyze_stock_mean_reversion
from strategies.backtest import run_backtest
from strategies.pairs_trading_analyzer import find_cointegrated_pairs, analyze_pair_spread

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

@st.cache_resource
def load_model():
    """Loads the trained ML model."""
    try:
        model = joblib.load("ml/xgb_model.joblib")
        return model
    except FileNotFoundError:
        return None

def plot_stock_chart(strategy_data, ticker_symbol):
    if strategy_data is None or len(strategy_data) < 2:
        fig = go.Figure()
        fig.update_layout(title=f'{ticker_symbol} - Not Enough Data to Display Chart', xaxis_visible=False, yaxis_visible=False)
        return fig
    
    start_price, end_price = strategy_data['Close'].iloc[0], strategy_data['Close'].iloc[-1]
    percent_change = ((end_price / start_price) - 1) * 100 if start_price != 0 else 0
    change_color = "green" if percent_change >= 0 else "red"
    chart_title = f"{ticker_symbol} Advanced Analysis | Period Change: <span style='color:{change_color};'>{percent_change:.2f}%</span>"

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
    
    # Dynamically find Bollinger Band column names if they exist
    bbu_col, bbm_col, bbl_col = next((c for c in strategy_data.columns if c.startswith('BBU_')), None), next((c for c in strategy_data.columns if c.startswith('BBM_')), None), next((c for c in strategy_data.columns if c.startswith('BBL_')), None)
    if all([bbu_col, bbm_col, bbl_col]):
        fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data[bbu_col], name='Upper Band', line=dict(color='gray', dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data[bbl_col], name='Lower Band', line=dict(color='gray', dash='dash'), fill='tonexty', fillcolor='rgba(128,128,128,0.1)'), row=1, col=1)
        fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data[bbm_col], name='Middle Band', line=dict(color='orange', dash='dash')), row=1, col=1)

    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['Close'], name='Close Price'), row=1, col=1)
    if 'SMA_10' in strategy_data.columns:
        fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_10'], name='Short SMA'), row=1, col=1)
    
    if 'MACD_12_26_9' in strategy_data.columns:
        fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['MACD_12_26_9'], name='MACD'), row=2, col=1)
        fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['MACDs_12_26_9'], name='Signal Line'), row=2, col=1)
        fig.add_trace(go.Bar(x=strategy_data.index, y=strategy_data['MACDh_12_26_9'], name='Histogram'), row=2, col=1)

    if 'RSI_14' in strategy_data.columns:
        fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['RSI_14'], name='RSI'), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="blue", row=3, col=1)

    fig.update_layout(title_text=chart_title, height=800, showlegend=True)
    fig.update_yaxes(title_text="Price", row=1, col=1), fig.update_yaxes(title_text="MACD", row=2, col=1), fig.update_yaxes(title_text="RSI", row=3, col=1)
    fig.update_xaxes(rangeslider_visible=True, row=1, col=1)
    return fig

def display_detailed_view(ticker, total_capital, risk_percent, analysis_function):
    try:
        with st.spinner(f"Fetching data for {ticker}..."):
            stock_data = fetch_daily_bars(ticker)
        
        if stock_data.empty:
            st.warning("No data found for this ticker.")
            return

        strategy_data = analysis_function(stock_data, ticker) if "Trend" in analysis_function.__name__ else analysis_function(stock_data)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.subheader("Key Metrics")
            last_row = strategy_data.iloc[-1]
            st.metric("Last Price", f"{last_row['Close']:.2f}")
            if 'RSI_14' in last_row: st.metric("RSI (14)", f"{last_row['RSI_14']:.2f}")
            if 'Signal_Score' in last_row: st.metric("Signal Score", f"{int(last_row['Signal_Score'])}/7")
            st.info(f"Recommendation: **{last_row['Recommendation']}**")

            if 'Relative_Strength' in last_row and pd.notna(last_row['Relative_Strength']):
                rs_delta = f"{last_row['Relative_Strength']:.2%}"
                st.metric("20-Day Relative Strength", value="Outperforming" if last_row['Relative_Strength'] > 0 else "Underperforming", delta=rs_delta)
            
            if 'Stop_Loss' in last_row:
                st.write("---")
                st.subheader("Risk & Position Sizing")
                st.metric("Stop-Loss", f"{last_row['Stop_Loss']:.2f}", f"-{last_row['Close'] - last_row['Stop_Loss']:.2f} (Risk)", delta_color="inverse")
                st.metric("Take-Profit", f"{last_row['Take_Profit']:.2f}", f"+{last_row['Take_Profit'] - last_row['Close']:.2f} (Reward)")
                risk_per_share = last_row['Close'] - last_row['Stop_Loss']
                if risk_per_share > 0 and total_capital > 0:
                    capital_to_risk = total_capital * (risk_percent / 100)
                    position_size = capital_to_risk / risk_per_share
                    st.metric("Suggested Shares", f"{position_size:.2f}", help=f"Risking {risk_percent}% of ${total_capital:,.2f}")

        with col2:
            fig = plot_stock_chart(strategy_data, ticker)
            st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("View Full Data and Signals"):
            st.dataframe(strategy_data)
    except Exception as e:
        st.error(f"An error occurred while analyzing {ticker}."), st.exception(e)

def calculate_portfolio_summary(portfolio):
    # (function is unchanged)
    pass

def run_app():
    st.set_page_config(page_title="Trading Dashboard", layout="wide")

    # Initialize all session state variables
    for key in ['portfolio', 'watchlist', 'screener_view_ticker', 'recommendations', 'found_pairs', 'ml_recommendations']:
        if key not in st.session_state:
            st.session_state[key] = [] if 'list' in key else None if 'ticker' in key else pd.DataFrame()

    with st.sidebar:
        st.title("💹 Trading Dashboard")
        st.info("A comprehensive tool for swing trading analysis.")
        
        st.write("---")
        st.header("Global Settings")
        selected_strategy = st.selectbox("Select Analysis Strategy", ["Trend-Following", "Mean-Reversion"])
        
        st.write("---")
        st.header("Risk Settings")
        total_capital = st.number_input("Total Trading Capital", 1000, step=1000, value=100000)
        risk_percent = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.0, 0.5)

        st.write("---")
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

    st.title(f"Nordic Market Analysis ({selected_strategy})")
    
    model = load_model()

    if selected_strategy == "Mean-Reversion":
        analysis_function = analyze_stock_mean_reversion
    else:
        analysis_function = analyze_stock

    tabs = st.tabs(["🏠 Dashboard", "📈 Screener", "💡 ML Suggestions", "🔍 Individual Analysis", "💼 Portfolio", "🔭 Watchlist", "🧪 Backtester", "➗ Pairs Trading"])

    with tabs[0]:
        # (Dashboard tab is unchanged)
        pass

    with tabs[1]:
        # (Screener tab is unchanged, but now uses the selected analysis_function)
        pass

    with tabs[2]:
        st.header("💡 ML Suggestion Engine")
        # (ML Suggestion tab is unchanged)
        pass

    with tabs[3]:
        st.header("🔍 Deep-Dive on a Single Stock")
        custom_ticker = st.text_input("Enter Any Ticker", key="custom_ticker").upper()
        if custom_ticker:
            display_detailed_view(custom_ticker, total_capital, risk_percent, analysis_function)

    with tabs[4]:
        st.header("💼 My Portfolio Tracker")
        # (Portfolio tab is unchanged, but passes new arguments to display_detailed_view)
        pass
        
    with tabs[5]:
        st.header("🔭 My Stock Watchlist")
        # (Watchlist tab is unchanged, but passes new arguments to display_detailed_view)
        pass

    with tabs[6]:
        st.header("🧪 Strategy Backtester")
        with st.form("backtest_form"):
            # ...
            if st.form_submit_button("Run Backtest"):
                # Pass the selected_strategy to the backtester
                stats, script, div = run_backtest(ticker, start_date, end_date, selected_strategy)
                # ...
    
    with tabs[7]:
        st.header("➗ Pairs Trading Screener")
        # (Pairs Trading tab is unchanged)
        pass

if __name__ == "__main__":
    run_app()
