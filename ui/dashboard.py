import streamlit as st
from data.fetchers.yahoo_fetcher import fetch
from screening.filters import apply_screen
import yaml

with open("config/config.yaml") as f:
    config = yaml.safe_load(f)

symbols = config.get("symbols", [])
rules = config.get("rules", {})

st.title("Stocks Swing Trade Dashboard")
search_symbol = st.sidebar.text_input("Enter symbol (e.g., AAPL, NOK.OL)", "")
selected_symbols = [search_symbol.upper()] if search_symbol else symbols

candidate_scores = []
for symbol in selected_symbols:
    df = fetch(symbol)
    if df.empty:
        st.warning(f"No data for {symbol}")
        continue
    passed, details = apply_screen(df, rules)
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
