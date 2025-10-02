# ui/dashboard.py

import streamlit as st
import pandas as pd

# This import is the one that was causing the error.
# It relies on the project being run from the root folder via main.py.
from data.fetchers.yahoo_fetcher import fetch

def run_app():
    """
    This is the main function that builds and runs the Streamlit dashboard.
    """

    # --- 1. Page Configuration ---
    # Set the title and icon that appear in the browser tab.
    st.set_page_config(
        page_title="Trading Dashboard",
        page_icon="💹",
        layout="wide"
    )

    # --- 2. Page Title ---
    # Display a title at the top of the app.
    st.title("Simple Stock Price Dashboard")

    # --- 3. Sidebar for User Input ---
    # Use the sidebar for inputs to keep the main area clean.
    st.sidebar.header("User Input")
    
    # Get the stock ticker from the user. Default to 'AAPL'.
    ticker_symbol = st.sidebar.text_input(
        label="Enter Stock Ticker",
        value="AAPL"
    ).upper()

    # --- 4. Main Content Area ---
    # Only proceed if the user has entered a ticker symbol.
    if ticker_symbol:
        st.header(f"Displaying data for: {ticker_symbol}")

        try:
            # Use a spinner to show a loading message while fetching data.
            with st.spinner(f"Fetching data for {ticker_symbol}..."):
                stock_data = fetch(ticker_symbol)

            # Check if the fetch function returned a non-empty DataFrame.
            if not stock_data.empty:
                # --- Display Charts and Data ---
                st.subheader("Closing Price History")
                # Assuming the DataFrame has a 'Close' column for the price.
                st.line_chart(stock_data['Close'])

                st.subheader("Recent Stock Data")
                # Display the raw data in a table.
                st.dataframe(stock_data)
            else:
                st.warning("No data returned for this ticker. Please check the symbol.")

        except Exception as e:
            # Display a friendly error message if the fetch fails for any reason.
            st.error(f"An error occurred: {e}")
    else:
        # Show a message if the text input is empty.
        st.info("Please enter a stock ticker in the sidebar to get started.")

# This standard Python block allows you to run this script directly for testing.
# For example: `python ui/dashboard.py` from your project's root directory.
if __name__ == "__main__":
    run_app()
