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
        fig.update_layout(title=f'{ticker_symbol} - Not Enough Data to Display Chart', xaxis_visible=False, yaxis_visible=False)
        return fig
    
    start_price, end_price = strategy_data['Close'].iloc[0], strategy_data['Close'].iloc[-1]
    percent_change = ((end_price / start_price) - 1) * 100 if start_price != 0 else 0
    change_color = "green" if percent_change >= 0 else "red"
    chart_title = f"{ticker_symbol} Analysis | Change: <span style='color:{change_color};'>{percent_change:.2f}%</span>"

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
    
    # Bollinger Bands
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['BBU_20_2.0'], name='Upper Band', line=dict(color='gray', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['BBL_20_2.0'], name='Lower Band', line=dict(color='gray', dash='dash'), fill='tonexty', fillcolor='rgba(128,128,128,0.1)'), row=1, col=1)
    
    # Price and SMAs
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['Close'], name='Close Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['SMA_10'], name='Short SMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['BBM_20_2.0'], name='Middle Band'), row=1, col=1) # Middle BBand
    
    # MACD
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['MACD_12_26_9'], name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['MACDs_12_26_9'], name='Signal Line'), row=2, col=1)
    fig.add_trace(go.Bar(x=strategy_data.index, y=strategy_data['MACDh_12_26_9'], name='Histogram'), row=2, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=strategy_data.index, y=strategy_data['RSI_14'], name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="blue", row=3, col=1)

    fig.update_layout(title_text=chart_title, height=800, showlegend=True)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    fig.update_xaxes(rangeslider_visible=True, row=1, col=1)
    return fig

def display_detailed_view(ticker, total_capital, risk_percent):
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
            st.metric("Signal Score", f"{int(last_row['Signal_Score'])}/7")
            st.info(f"Recommendation: **{last_row['Recommendation']}**")

            if 'Relative_Strength' in last_row and pd.notna(last_row['Relative_Strength']):
                rs_delta = f"{last_row['Relative_Strength']:.2%}"
                st.metric("20-Day Relative Strength", value="Outperforming" if last_row['Relative_Strength'] > 0 else "Underperforming", delta=rs_delta)
            
            st.write("---")
            st.subheader("Risk & Position Sizing")
            st.metric("Stop-Loss", f"{last_row['Stop_Loss']:.2f}", f"-{last_row['Close'] - last_row['Stop_Loss']:.2f} (Risk)", delta_color="inverse")
            st.metric("Take-Profit", f"{last_row['Take_Profit']:.2f}", f"+{last_row['Take_Profit'] - last_row['Close']:.2f} (Reward)")
            
            risk_per_share = last_row['Close'] - last_row['Stop_Loss']
            if risk_per_share > 0 and total_capital > 0:
                capital_to_risk = total_capital * (risk_percent / 100)
                position_size = capital_to_risk / risk_per_share
                position_value = position_size * last_row['Close']
                st.metric("Suggested Shares", f"{position_size:.2f}", help=f"Risking {risk_percent}% of ${total_capital:,.2f}")
                st.metric("Position Value", f"{position_value:,.2f} SEK")
            else:
                st.warning("Cannot calculate position size.")

        with col2:
            fig = plot_stock_chart(strategy_data, ticker)
            st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("View Full Data and Signals"):
            st.dataframe(strategy_data)
    except Exception as e:
        st.error(f"An error occurred while analyzing {ticker}."), st.exception(e)

def calculate_portfolio_summary(portfolio):
    # (This function is unchanged)
    pass

def run_app():
    st.set_page_config(page_title="Trading Dashboard", layout="wide")

    if 'portfolio' not in st.session_state: st.session_state.portfolio = []
    if 'watchlist' not in st.session_state: st.session_state.watchlist = []
    if 'screener_view_ticker' not in st.session_state: st.session_state.screener_view_ticker = None

    with st.sidebar:
        st.title("💹 Trading Dashboard")
        st.info("Swing trading analysis for Nordic markets."), st.write("---")
        
        st.header("Risk Settings")
        total_capital = st.number_input("Total Trading Capital", min_value=1000, step=1000, value=100000)
        risk_percent = st.slider("Risk per Trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

        st.write("---")
        st.header("My Data")
        uploaded_file = st.file_uploader("Import Data (JSON)", type=['json'])
        if uploaded_file:
            # (Import logic is unchanged)
            pass
        if st.session_state.portfolio or st.session_state.watchlist:
            # (Export logic is unchanged)
            pass
        st.write("---"), st.warning("Disclaimer: Not financial advice.")

    st.title("Nordic Market Swing Trading Analysis")
    
    tabs = st.tabs(["🏠 Dashboard", "📈 Screener", "🔍 Individual Analysis", "💼 Portfolio", "🔭 Watchlist", "🧪 Backtester"])

    with tabs[0]:
        # (Dashboard tab is unchanged)
        pass

    with tabs[1]:
        # (Screener tab is unchanged)
        pass

    with tabs[2]:
        st.header("Deep-Dive on a Single Stock")
        custom_ticker = st.text_input("Enter Any Ticker", key="custom_ticker").upper()
        if custom_ticker:
            display_detailed_view(custom_ticker, total_capital, risk_percent)

    with tabs[3]:
        # (Portfolio tab is unchanged but needs new arguments for display_detailed_view)
        if selected_ticker:
            display_detailed_view(selected_ticker, total_capital, risk_percent)

    with tabs[4]:
        # (Watchlist tab is unchanged but needs new arguments for display_detailed_view)
        if selected_ticker_wl:
            display_detailed_view(selected_ticker_wl, total_capital, risk_percent)
            
    with tabs[5]:
        # (Backtester tab is unchanged)
        pass

if __name__ == "__main__":
    run_app()
