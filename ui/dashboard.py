import streamlit as st
import pandas as pd
import os
import yaml

from data.fetchers.yahoo_fetcher import fetch
from indicators.rsi import calculate_rsi
from indicators.bollinger import calculate_bollinger
from indicators.macd import calculate_macd

# Load config
config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

st.title("📊 OMXS30 Swing Trade Dashboard")

tickers = config["omxs30"]["tickers"]
results = []

st.write("🔍 Fetching and analyzing data... Please wait.")

for ticker in tickers:
    try:
        df = fetch(ticker, period="6mo", interval="1d")
        if df.empty:
            st.warning(f"No data for {ticker}")
            continue

        df["RSI"] = calculate_rsi(df["Close"])
        df["Upper"], df["Lower"] = calculate_bollinger(df["Close"])
        macd, signal = calculate_macd(df["Close"])
        df["MACD"], df["Signal"] = macd, signal

        latest = df.iloc[-1]

        # Signal logic
        if latest["RSI"] < 30 and latest["Close"] < latest["Lower"]:
            signal_text = "Strong Buy"
        elif latest["RSI"] > 70 and latest["Close"] > latest["Upper"]:
            signal_text = "Strong Sell"
        else:
            signal_text = "Neutral"

        results.append({
            "Ticker": ticker,
            "Close": round(latest["Close"], 2),
            "RSI": round(latest["RSI"], 2),
            "Signal": signal_text,
            "Entry Point": round(latest["Close"] * 0.98, 2),
            "Exit Point": round(latest["Close"] * 1.05, 2),
        })

    except Exception as e:
        st.error(f"Error processing {ticker}: {e}")

# ✅ Show top candidates
if results:
    df = pd.DataFrame(results)
    st.subheader("Top Swing Trade Candidates (sorted by RSI)")
    st.dataframe(df.sort_values(by=["RSI"], ascending=True))
else:
    st.warning("⚠️ No results available. Possibly tickers or data fetching failed.")

# ✅ Always show all analyzed stocks
st.subheader("All Analyzed Stocks")
if results:
    st.dataframe(pd.DataFrame(results))
else:
    st.write("No stock data analyzed.")
