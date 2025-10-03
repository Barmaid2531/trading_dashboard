import streamlit as st
import os

st.set_page_config(layout="wide")
st.title("File Structure Diagnostic")

# Define the root path based on previous tracebacks
root_path = "/mount/src/trading_dashboard/"

st.write(f"**Checking project structure inside:** `{root_path}`")
st.write("---")

# --- 1. Check Root Folder ---
st.subheader("1. Root Folder Contents")
try:
    root_contents = os.listdir(root_path)
    st.code(root_contents)
except Exception as e:
    st.error(f"Could not list contents of root folder: {e}")

# --- 2. Check 'data' Folder ---
st.subheader("2. `data` Folder Contents")
data_path = os.path.join(root_path, "data")
try:
    data_contents = os.listdir(data_path)
    st.code(data_contents)
    if "__init__.py" in data_contents:
        st.success("`__init__.py` found in `data/`")
    else:
        st.error("`__init__.py` NOT FOUND in `data/`")
except Exception as e:
    st.error(f"Could not list contents of 'data' folder. Does it exist? Error: {e}")

# --- 3. Check 'data/fetchers' Folder ---
st.subheader("3. `data/fetchers` Folder Contents")
fetchers_path = os.path.join(data_path, "fetchers")
try:
    fetchers_contents = os.listdir(fetchers_path)
    st.code(fetchers_contents)
    if "__init__.py" in fetchers_contents:
        st.success("`__init__.py` found in `data/fetchers/`")
    else:
        st.error("`__init__.py` NOT FOUND in `data/fetchers/`")
        
    if "yfinance_fetcher.py" in fetchers_contents:
        st.success("`yfinance_fetcher.py` found.")
    else:
        st.error("`yfinance_fetcher.py` NOT FOUND.")
except Exception as e:
    st.error(f"Could not list contents of 'data/fetchers' folder. Does it exist? Error: {e}")

st.write("---")
st.info("Please copy all the text from this page and paste it in our chat.")
