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
        "OMXS30 (Sweden)": [
            'ERIC-B.ST', 'ADDT-B.ST', 'SCA-B.ST', 'AZN.ST', 'BOL.ST', 'SAAB-B.ST', 'NDA-SE.ST', 'SKA-B.ST',
            'TEL2-B.ST', 'HM-B.ST', 'TELIA.ST', 'NIBE-B.ST', 'LIFCO-B.ST', 'SHB-A.ST', 'SEB-A.ST', 'ESSITY-B.ST',
            'SWED-A.ST', 'EVO.ST', 'SKF-B.ST', 'INDU-C.ST', 'SAND.ST', 'VOLV-B.ST', 'HEXA-B.ST', 'ABB.ST',
            'ASSA-B.ST', 'EPI-A.ST', 'INVE-B.ST', 'EQT.ST', 'ALFA.ST', 'ATCO-A.ST'
        ],
        "OMXC25 (Denmark)": [
            'MAERSK-B.CO', 'NOVO-B.CO', 'DSV.CO', 'VWS.CO', 'PNDORA.CO', 'GN.CO', 'ORSTED.CO', 'DANSKE.CO',
            'NZYM-B.CO', 'GMAB.CO', 'TRYG.CO', 'CARL-B.CO', 'COLOB.CO', 'CHR.CO', 'JYSK.CO', 'RBREW.CO',
            'ROCK-B.CO', 'ISS.CO', 'DEMANT.CO', 'AMBU-B.CO', 'BAVA.CO', 'NETC.CO', 'NDA-DK.CO', 'SYDB.CO', 'FLS.CO'
        ],
        "OMXH25 (Finland)": [
            'NOKIA.HE', 'SAMPO.HE', 'KNEBV.HE', 'FORTUM.HE', 'UPM.HE', 'NESTE.HE', 'STERV.HE', 'ELISA.HE',
            'WRT1V.HE', 'OUT1V.HE', 'TIETO.HE', 'ORNBV.HE', 'HUH1V.HE', 'CGCBV.HE', 'KESKOB.HE', 'MOCORP.HE',
            'VALMT.HE', 'YIT.HE', 'KCR.HE', 'TELIA1.HE', 'NDA-FI.HE', 'SSABBH.HE', 'METSO.HE', 'QTCOM.HE', 'KOJAMO.HE'
        ],
        "OBX (Norway)": [
            'EQNR.OL', 'DNB.OL', 'TEL.OL', 'MOWI.OL', 'AKERBP.OL', 'YAR.OL', 'NHY.OL', 'ORK.OL',
            'SUBC.OL', 'SALM.OL', 'AKSO.OL', 'SCHA.OL', 'NEL.OL', 'FRO.OL', 'STB.OL', 'NOD.OL', 
            'GJF.OL', 'RECSI.OL', 'BWO.OL', 'NAS.OL', 'OTL.OL', 'SCATC.OL', 'TGS.OL'
        ]
    }
    return indices

def plot_stock_chart(strategy_data, ticker_symbol):
    if strategy_data is None or len(strategy_data) < 2:
        fig = go.Figure()
        fig.update_layout(title=f'{ticker_symbol} - Not Enough Data to Display Chart', xaxis_visible=False, yaxis_visible=False)
        return fig
    
    start_price = strategy_data['Close'].iloc[0]
    end_price = strategy_data['Close'].iloc[-1]
    percent_change = ((end_price / start_price) - 1) * 100 if start_price != 0 else 0
    change_color = "green" if percent_change >= 0 else "red"
    chart_title = f"{ticker_symbol} Advanced Analysis | Period Change: <span style='color:{change_color};'>{percent_change:.2f}%</span>"

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
            st.metric("MACD Hist", f"{last_row['MACDh_12_26_9']:.2f}")
            st.metric("Signal Score", f"{int(last_row['Signal_Score'])}/5", help="Based on SMA, MACD, RSI, OBV, and Daily Trend.")
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
    st.set_page_config(page_title="Trading Dashboard", layout="wide")

    if 'portfolio' not in st.session_state: st.session_state.portfolio = []
    if 'watchlist' not in st.session_state: st.session_state.watchlist = []

    with st.sidebar:
        st.title("💹 Trading Dashboard")
        st.info("Swing trading analysis for Nordic markets.")
        st.write("---")
        st.header("My Data")
        uploaded_file = st.file_uploader("Import Data (JSON)", type=['json'])
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                st.session_state.portfolio = data.get('portfolio', [])
                st.session_state.
