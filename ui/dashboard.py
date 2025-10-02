import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import yaml
from data.fetchers.yahoo_fetcher import fetch
from screening.filters import apply_screen


config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

symbols = config.get("symbols", [])
rules = config.get("rules", {})

st.title("Stocks Swing Trade Dashboard")
st.write("Streamlit app loaded")
st.write(f"Config symbols: {symbols}")

search_symbol = st.sidebar.text_input("Enter symbol (e.g., AAPL, NOK.OL)", "")
selected_symbols = [search_symbol.upper()] if search_symbol else symbols

candidate_scores = []

for symbol in selected_symbols:
    df = fetch(symbol)
    if df.empty:
        st.warning(f"No data found for {symbol}")
        continue

    try:
        passed, details = apply_screen(df, rules)
    except Exception as e:
        st.error(f"Error applying screen for {symbol}: {e}")
        continue

    score = sum(1 for v in details.values() if v['passed'])
    candidate_scores.append({"Symbol": symbol, "Score": score, "Passed": passed, "Details": details})

    st.subheader(symbol)
    st.write(f"Passes Swing Trade Criteria: {passed}")
    st.line_chart(df['Close'])

if candidate_scores:
    ranked_candidates = sorted(candidate_scores, key=lambda x: x['Score'], reverse=True)
    st.header("Top Swing Trade Candidates")
    top_table = [{"Symbol": c["Symbol"], "Score": c["Score"], "Passed": c["Passed"]} for c in ranked_candidates]
    st.table(top_table)
