import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from data.fetchers.yahoo_fetcher import fetch
from data.fetchers.index_fetcher import get_omxs30_tickers
from indicators.rsi import calculate_rsi
from indicators.macd import calculate_macd
from indicators.bollinger import calculate_bollinger_bands

st.title("OMXS30 Swing Trade Dashboard (DEBUG MODE)")

# Step 1: Fetch OMXI30 tickers dynamically
symbols = get_omxs30_tickers()
st.write("✅ Fetched symbols:", symbols)

def analyze_stock(symbol):
    try:
        df = fetch(symbol, period="6mo", interval="1d")
        if df is None or df.empty:
            st.warning(f"⚠️ No data for {symbol}")
            return None

        df["RSI"] = calculate_rsi(df["Close"])
        df["MACD"], df["Signal"], df["Hist"] = calculate_macd(df["Close"])
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
    except Exception as e:
        st.error(f"❌ Error analyzing {symbol}: {e}")
        return None

results = []
for sym in symbols:
    st.write(f"🔍 Analyzing {sym}...")
    res = analyze_stock(sym)
    if res:
        results.append(res)

st.write("📊 Raw analysis results:", results)

if results:
    df = pd.DataFrame(results)
    st.subheader("Top Swing Trade Candidates (OMXS30)")
    st.dataframe(df.sort_values(by=["Signal", "RSI"], ascending=[True, True]))
else:
    st.warning("⚠️ No results available. Possibly tickers or data fetching failed.")
