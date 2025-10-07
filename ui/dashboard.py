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
        fig.update_layout(title=f'{ticker_symbol} - Not Enough Data', xaxis_visible=False, yaxis_visible=False)
        return fig
    
    start_price, end_price = strategy_data['Close'].iloc[0], strategy_data['Close'].iloc[-1]
    percent_change = ((end_price / start_price) - 1) * 100 if start_price != 0 else 0
    change_color = "green" if percent_change >= 0 else "red"
    chart_title = f"{ticker_symbol} Analysis | Change: <span style='color:{change_color};'>{percent_change:.2f}%</span>"

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
    
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

        strategy_data = analysis_function(stock_data, ticker) if "advanced_analyzer" in analysis_function.__module__ else analysis_function(stock_data)
        
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

@st.cache_data
def calculate_portfolio_summary(portfolio):
    total_value_sek, total_investment_sek = 0, 0
    if not portfolio:
        return 0, 0, 0, 0
    for holding in portfolio:
        try:
            currency = yf.Ticker(holding["ticker"]).info.get('currency', 'SEK')
            data = fetch_daily_bars(holding["ticker"], period="5d")
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                fx_rate = get_fx_rate(currency, 'SEK')
                if fx_rate is None: fx_rate = 1.0
                total_investment_sek += (holding["quantity"] * holding["gav"]) * fx_rate
                total_value_sek += (holding["quantity"] * current_price) * fx_rate
        except Exception:
            continue
    total_pl_sek = total_value_sek - total_investment_sek
    total_pl_pct = (total_pl_sek / total_investment_sek) * 100 if total_investment_sek != 0 else 0
    return total_value_sek, total_investment_sek, total_pl_sek, total_pl_pct

def generate_pros_cons(data):
    pros, cons = [], []
    last_row = data.iloc[-1]
    if last_row.get('Signal_Score', 0) >= 5: pros.append(f"High Signal Score ({int(last_row['Signal_Score'])}/7)")
    if last_row.get('SMA_10', 0) > last_row.get('SMA_50', 0): pros.append("Positive Trend (SMA10 > SMA50)")
    if last_row.get('MACDh_12_26_9', 0) > 0: pros.append("Increasing Momentum (MACD > 0)")
    if last_row.get('Relative_Strength', 0) > 0: pros.append("Outperforming Market")
    if last_row.get('RSI_14', 100) < 60: pros.append("Not Overbought (RSI < 60)")
    if last_row.get('RSI_14', 0) > 70: cons.append("Nearing Overbought (RSI > 70)")
    atr_percent = (last_row.get('ATRr_14', 0) / last_row.get('Close', 1)) * 100
    if atr_percent > 4: cons.append(f"High Volatility (ATR is {atr_percent:.1f}%)")
    if not pros: pros.append("No outstanding positive indicators.")
    if not cons: cons.append("No significant negative indicators.")
    return pros, cons

def run_app():
    st.set_page_config(page_title="Trading Dashboard", layout="wide")

    for key in ['portfolio', 'watchlist', 'screener_view_ticker', 'recommendations', 'found_pairs', 'ml_recommendations']:
        if key not in st.session_state:
            st.session_state[key] = [] if ('list' in key or 'portfolio' in key) else None if 'ticker' in key else pd.DataFrame()

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
            if not st.session_state.recommendations.empty:
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
            display_detailed_view(st.session_state.screener_view_ticker, total_capital, risk_percent, analysis_function)
            if st.button("⬅️ Back to Screener Results"):
                st.session_state.screener_view_ticker = None; st.rerun()
        else:
            nordic_indices = get_nordic_indices()
            selected_index = st.selectbox("Select an Index to Scan:", options=list(nordic_indices.keys()))
            if st.button(f"Scan {selected_index} for Signals", type="primary"):
                tickers_to_scan = nordic_indices[selected_index]
                signals = []
                progress_bar = st.progress(0)
                for i, ticker in enumerate(tickers_to_scan):
                    progress_bar.progress((i + 1) / len(tickers_to_scan), f"Scanning {ticker}...")
                    try:
                        data = fetch_daily_bars(ticker, period="1y")
                        if not data.empty and len(data) > 50:
                            strategy_data = analysis_function(data, ticker) if selected_strategy == "Trend-Following" else analysis_function(data)
                            last_row = strategy_data.iloc[-1]
                            if "Buy" in last_row['Recommendation']:
                                row_data = {'Ticker': ticker, 'Recommendation': last_row['Recommendation']}
                                if 'Signal_Score' in last_row: row_data['Signal Score'] = f"{int(last_row['Signal_Score'])}/7"
                                signals.append(row_data)
                    except Exception: continue
                progress_bar.empty()
                st.session_state.recommendations = pd.DataFrame(signals)

            if not st.session_state.recommendations.empty:
                df = st.session_state.recommendations
                st.metric("Buy Signals Found", len(df))
                st.write("---")
                for _, row in df.iterrows():
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
                        c1.subheader(row['Ticker'])
                        c2.info(row['Recommendation'])
                        if 'Signal Score' in row: c3.metric("Signal Score", row['Signal Score'])
                        if c4.button("Analyze", key=row['Ticker']):
                            st.session_state.screener_view_ticker = row['Ticker']; st.rerun()
            else:
                st.info(f"No '{selected_strategy}' signals found in this index.")

    with tabs[2]:
        st.header("💡 ML Suggestion Engine")
        if model is None:
            st.error("ML model file ('ml/xgb_model.joblib') not found. Please run `ml/trainer.py` to generate the model file and upload it to the `ml/` folder in your repository.")
        else:
            c1, c2 = st.columns(2)
            investment_amount = c1.number_input("Amount to Invest", 100, step=100, value=1000)
            nordic_indices = get_nordic_indices()
            index_to_scan = c2.selectbox("Select Index to Scan:", list(nordic_indices.keys()), key="ml_suggestion_index")
            confidence_threshold = st.slider("Minimum Confidence (%)", 0, 100, 70)

            if st.button("Find ML-Powered Opportunities", type="primary"):
                tickers = nordic_indices[index_to_scan]
                ml_buys_list = []
                progress_bar = st.progress(0)
                
                with st.spinner(f"Scanning {index_to_scan} with ML model..."):
                    for i, ticker in enumerate(tickers):
                        progress_bar.progress((i + 1) / len(tickers), f"Scanning {ticker}...")
                        try:
                            data = fetch_daily_bars(ticker, period="1y")
                            if not data.empty and len(data) > 50:
                                ml_data = analyze_stock_ml(data.copy(), model)
                                if not ml_data.empty:
                                    last_row_ml = ml_data.iloc[-1]
                                    if last_row_ml['ML_Prediction'] == 1 and last_row_ml['ML_Confidence'] * 100 >= confidence_threshold:
                                        # Also run the rule-based analyzer to get stop-loss info
                                        rule_data = analyze_stock(data.copy(), ticker)
                                        ml_buys_list.append({
                                            "Ticker": ticker, 
                                            "Data": rule_data.iloc[-1], 
                                            "Confidence": last_row_ml['ML_Confidence']
                                        })
                        except Exception:
                            continue
                
                progress_bar.empty()
                # --- FIX: Convert the list to a DataFrame ---
                st.session_state.ml_recommendations = pd.DataFrame(ml_buys_list)

            if not st.session_state.ml_recommendations.empty:
                recommendations_df = st.session_state.ml_recommendations
                st.metric("ML Buy Signals Found", len(recommendations_df))
                
                # Sort by confidence
                recommendations_df = recommendations_df.sort_values(by="Confidence", ascending=False)
                st.success(f"Displaying the top {len(recommendations_df)} opportunities:")

                # --- FIX: Iterate over the DataFrame using .iterrows() ---
                for _, row in recommendations_df.iterrows():
                    ticker, last_row, confidence = row['Ticker'], row['Data'], row['Confidence']
                    with st.container(border=True):
                        st.subheader(f"{ticker}")
                        st.metric("Model Confidence", f"{confidence * 100:.2f}%")
                        
                        st.markdown("**Suggested Trade Plan:**")
                        shares_to_buy = investment_amount / last_row['Close']
                        
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Entry Price", f"{last_row['Close']:.2f}")
                        c2.metric("Stop-Loss", f"{last_row['Stop_Loss']:.2f}")
                        c3.metric("Take-Profit", f"{last_row['Take_Profit']:.2f}")
                        c4.metric(f"Shares for {investment_amount}", f"{shares_to_buy:.2f}")
            else:
                 st.info("Click the button to scan for ML-powered opportunities.")
    with tabs[2]:
        st.header("💡 ML Suggestion Engine")
        if model is None:
            st.error("ML model file ('ml/xgb_model.joblib') not found. Please run `ml/trainer.py` to generate the model file.")
        else:
            c1, c2 = st.columns(2)
            investment_amount = c1.number_input("Amount to Invest", 100, step=100, value=1000)
            nordic_indices = get_nordic_indices()
            index_to_scan = c2.selectbox("Select Index to Scan:", list(nordic_indices.keys()), key="ml_suggestion_index")
            confidence_threshold = st.slider("Minimum Confidence (%)", 0, 100, 70)
    
            if st.button("Find ML-Powered Opportunities", type="primary"):
                st.session_state.ml_scan_run = True # Set the flag that a scan has been run
                tickers = nordic_indices[index_to_scan]
                ml_buys_list = []
    
                with st.spinner(f"Scanning {index_to_scan} with ML model..."):
                    progress_bar = st.progress(0)
                    for i, ticker in enumerate(tickers):
                        progress_bar.progress((i + 1) / len(tickers), f"Scanning {ticker}...")
                        try:
                            data = fetch_daily_bars(ticker, period="1y")
                            if not data.empty and len(data) > 50:
                                ml_data = analyze_stock_ml(data.copy(), model)
                                if not ml_data.empty:
                                    last_row_ml = ml_data.iloc[-1]
                                    if last_row_ml['ML_Prediction'] == 1 and last_row_ml['ML_Confidence'] * 100 >= confidence_threshold:
                                        rule_data = analyze_stock(data.copy(), ticker)
                                        ml_buys_list.append({"Ticker": ticker, "Data": rule_data.iloc[-1], "Confidence": last_row_ml['ML_Confidence']})
                        except Exception:
                            continue
    
                progress_bar.empty()
                st.session_state.ml_recommendations = pd.DataFrame(ml_buys_list)
                st.rerun() # Force a clean rerun to display results correctly
    
            # --- NEW DISPLAY LOGIC ---
            if st.session_state.ml_scan_run:
                recommendations_df = st.session_state.ml_recommendations
                st.metric("ML Buy Signals Found", len(recommendations_df))
    
                if not recommendations_df.empty:
                    recommendations_df = recommendations_df.sort_values(by="Confidence", ascending=False)
                    st.success(f"Displaying the top {len(recommendations_df)} opportunities:")
                    for _, row in recommendations_df.iterrows():
                        ticker, last_row, confidence = row['Ticker'], row['Data'], row['Confidence']
                        with st.container(border=True):
                            st.subheader(f"{ticker}")
                            st.metric("Model Confidence", f"{confidence * 100:.2f}%")
                            st.markdown("**Suggested Trade Plan:**")
                            shares_to_buy = investment_amount / last_row['Close']
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Entry Price", f"{last_row['Close']:.2f}"), c2.metric("Stop-Loss", f"{last_row['Stop_Loss']:.2f}"),
                            c3.metric("Take-Profit", f"{last_row['Take_Profit']:.2f}"), c4.metric(f"Shares for {investment_amount}", f"{shares_to_buy:.2f}")
                else:
                    st.warning("Scan complete. No stocks currently meet the specified criteria.")
            else:
                st.info("Click the button to scan for ML-powered opportunities.")

    with tabs[4]:
        st.header("💼 My Portfolio Tracker")
        with st.form("add_holding_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            ticker, qty, gav = c1.text_input("Ticker").upper(), c2.number_input("Quantity", 0.01, format="%.2f"), c3.number_input("GAV", 0.01, format="%.2f")
            if st.form_submit_button("Add to Portfolio"):
                if ticker and qty > 0 and gav > 0:
                    st.session_state.portfolio.append({"ticker": ticker, "quantity": qty, "gav": gav}); st.success(f"Added {ticker}!")
        
        if st.session_state.portfolio:
            portfolio_data, total_value_sek, total_investment_sek = [], 0, 0
            with st.spinner("Updating portfolio with FX rates..."):
                for holding in st.session_state.portfolio:
                    try:
                        info = yf.Ticker(holding["ticker"]).info
                        currency = info.get('currency', 'SEK')
                        data = fetch_daily_bars(holding["ticker"])
                        if data.empty: continue
                        strategy_data = analysis_function(data, holding["ticker"]) if selected_strategy == "Trend-Following" else analysis_function(data)
                        last_row = strategy_data.iloc[-1]
                        current_price = last_row['Close']
                        fx_rate = get_fx_rate(currency, 'SEK')
                        if fx_rate is None: fx_rate = 1.0
                        
                        inv_local, val_local = (holding["quantity"] * holding["gav"]), (holding["quantity"] * current_price)
                        val_sek, inv_sek = val_local * fx_rate, inv_local * fx_rate
                        pl_sek, pl_pct = val_sek - inv_sek, (val_sek / inv_sek - 1) * 100 if inv_sek != 0 else 0

                        portfolio_data.append({
                            "Ticker": holding["ticker"], "Qty": holding["quantity"], "Currency": currency,
                            "GAV (Local)": f"{holding['gav']:.2f}", "Price (Local)": f"{current_price:.2f}",
                            "Value (SEK)": f"{val_sek:,.2f}", "P/L (SEK)": f"{pl_sek:,.2f}",
                            "P/L %": f"{pl_pct:.2f}%", "Suggestion": last_row['Recommendation']
                        })
                        total_value_sek, total_investment_sek = total_value_sek + val_sek, total_investment_sek + inv_sek
                    except Exception: continue
            
            if portfolio_data:
                total_pl_sek, total_pl_pct = total_value_sek - total_investment_sek, (total_value_sek / total_investment_sek - 1) * 100 if total_investment_sek != 0 else 0
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Portfolio Value", f"{total_value_sek:,.2f} SEK"), c2.metric("Total P/L", f"{total_pl_sek:,.2f} SEK"), c3.metric("Total P/L %", f"{total_pl_pct:.2f}%")
                st.write("---")
                def style_table(df):
                    def color(val, sugg=False):
                        if sugg: return f'color: {"green" if "Buy" in str(val) else "red" if "Sell" in str(val) else "white"}'
                        try: num = float(str(val))
                        except (ValueError, TypeError): return ''
                        return f'color: {"green" if num > 0 else "red" if num < 0 else "white"}'
                    return df.style.format({"P/L %": "{:.2f}%"}).applymap(lambda v: color(v, sugg=True), subset=['Suggestion']).applymap(lambda v: color(v, sugg=False), subset=['P/L (SEK)', 'P/L %'])
                st.dataframe(style_table(pd.DataFrame(portfolio_data)), use_container_width=True)

                st.write("---")
                st.subheader("Manage & Analyze Portfolio")
                portfolio_tickers = [h['ticker'] for h in st.session_state.portfolio]
                selected_ticker = st.selectbox("Select a holding:", [""] + portfolio_tickers, key="portfolio_select")
                if selected_ticker:
                    display_detailed_view(selected_ticker, total_capital, risk_percent, analysis_function)
                    st.write("---"), st.write(f"Editing **{selected_ticker}**")
                    idx = portfolio_tickers.index(selected_ticker)
                    holding_to_edit = st.session_state.portfolio[idx]
                    c1, c2 = st.columns(2)
                    new_qty, new_gav = c1.number_input("New Qty", value=holding_to_edit['quantity'], key=f"qty_{selected_ticker}"), c2.number_input("New GAV", value=holding_to_edit['gav'], key=f"gav_{selected_ticker}")
                    c1, c2 = st.columns([1, 1])
                    if c1.button("Update", key=f"up_{selected_ticker}"):
                        st.session_state.portfolio[idx] = {"ticker": selected_ticker, "quantity": new_qty, "gav": new_gav}; st.success(f"Updated {selected_ticker}!"); st.rerun()
                    if c2.button("Delete", key=f"del_{selected_ticker}"):
                        st.session_state.portfolio.pop(idx); st.warning(f"Deleted {selected_ticker}."); st.rerun()

    with tabs[5]:
        st.header("🔭 My Stock Watchlist")
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
                        strategy_data = analysis_function(data, ticker) if selected_strategy == "Trend-Following" else analysis_function(data)
                        last_row = strategy_data.iloc[-1]
                        row_data = {"Ticker": ticker, "Recommendation": last_row['Recommendation']}
                        if 'Signal_Score' in last_row: row_data['Signal Score'] = f"{int(last_row['Signal_Score'])}/7"
                        if 'Close' in last_row: row_data['Current Price'] = f"{last_row['Close']:.2f}"
                        watchlist_data.append(row_data)
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
                display_detailed_view(selected_ticker_wl, total_capital, risk_percent, analysis_function)
                if st.button("Remove from Watchlist"):
                    st.session_state.watchlist.remove(selected_ticker_wl); st.warning(f"Removed {selected_ticker_wl}."); st.rerun()

    with tabs[6]:
        st.header("🧪 Strategy Backtester")
        with st.form("backtest_form"):
            c1, c2, c3 = st.columns(3)
            ticker, start_date, end_date = c1.text_input("Ticker", "AAPL").upper(), c2.date_input("Start Date", pd.to_datetime("2023-01-01")), c3.date_input("End Date", pd.to_datetime("2024-01-01"))
            if st.form_submit_button("Run Backtest"):
                with st.spinner(f"Running backtest..."):
                    try:
                        stats, script, div = run_backtest(ticker, start_date, end_date, selected_strategy)
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
    
    with tabs[7]:
        st.header("➗ Pairs Trading Screener")
        nordic_indices = get_nordic_indices()
        index_to_scan = st.selectbox("Select an Index to Find Pairs In:", options=list(nordic_indices.keys()), key="pairs_index")
        if st.button(f"Find Cointegrated Pairs in {index_to_scan}"):
            with st.spinner("Scanning for pairs... This may take several minutes."):
                tickers = nordic_indices[index_to_scan]
                pairs_df = find_cointegrated_pairs(tickers)
                st.session_state.found_pairs = pairs_df
        if not st.session_state.found_pairs.empty:
            pairs_df = st.session_state.found_pairs
            st.metric("Cointegrated Pairs Found", len(pairs_df))
            if not pairs_df.empty:
                st.dataframe(pairs_df.sort_values(by='P-Value'), use_container_width=True)
                st.write("---"), st.subheader("Analyze Pair Spread")
                selected_pair = st.selectbox("Select a pair to analyze:", options=pairs_df['Pair'].tolist())
                if selected_pair:
                    ticker1, ticker2 = selected_pair.split('-')
                    with st.spinner(f"Analyzing spread for {selected_pair}..."):
                        analysis_df = analyze_pair_spread(ticker1, ticker2)
                    if not analysis_df.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=analysis_df.index, y=analysis_df['Z_Score'], name='Z-Score'))
                        fig.add_hline(y=2.0, line_dash="dash", line_color="red"), fig.add_hline(y=-2.0, line_dash="dash", line_color="green")
                        fig.update_layout(title=f"Z-Score of {selected_pair} Price Spread", yaxis_title="Z-Score")
                        st.plotly_chart(fig, use_container_width=True)
                        st.info("Strategy: Short the spread when Z-Score > 2. Long the spread when Z-Score < -2.")
            else:
                st.warning("No cointegrated pairs found in this index.")

if __name__ == "__main__":
    run_app()
