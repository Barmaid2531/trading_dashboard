import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import yaml
from data.fetchers.yahoo_fetcher import fetch
from data.fetchers.index_fetcher import get_omxs30_tickers
from screening.filters import apply_screen
from indicators.rsi import calculate_rsi
from indicators.macd import calculate_macd
from indicators.bollinger import calculate_bollinger_bands

st.title("OMXS30 Swing Trade Dashboard")

# Step 1: Fetch OMXI30 tickers dynamically
symbols = get_omxs30_tickers()
st.sidebar.write("Loaded OMXI30 Symbols:", symbols)

def analyze_stock(symbol):
    df = fetch(symbol, period="6mo", interval="1d")
    if df is None or df.empty:
        return None

    df["RSI"] = calculate_rsi(df["Close"])
    df["MACD"], df["Signal"] = calculate_macd(df["Close"])
    df["Upper"], df["Lower"] = calculate_bollinger_bands(df["Close"])

    last = df.iloc[-1]
    signal, entry, exit = "Neutral", None, None

    if last["RSI"] < 30 and last["Close"] <= last["Lower"]:
        signal, entry = "Strong Buy", last["Close"]
    elif last["RSI"] > 70 and last["Close"] >= last["Upper"]:
        signal, exit = "Sell", last["Close"]
    elif last["MACD"] > last["Signal"]:
        signal = "Buy"
    elif last["MACD"] < last["Signal"]:
        signal = "Weak Sell"

    return {
        "Symbol": symbol,
        "Signal": signal,
        "Entry Point": entry,
        "Exit Point": exit,
        "RSI": round(last["RSI"], 2),
        "Price": last["Close"]
    }

results = []
for sym in symbols:
    res = analyze_stock(sym)
    if res:
        results.append(res)

if results:
    df = pd.DataFrame(results)
    st.subheader("Top Swing Trade Candidates (OMXI30)")
    st.dataframe(df.sort_values(by=["Signal", "RSI"], ascending=[True, True]))
else:
    st.warning("No results. Check data fetching.")
