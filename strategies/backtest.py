from backtesting import Backtest, Strategy
import yfinance as yf
import pandas as pd
from strategies.advanced_analyzer import analyze_stock

class AdvancedStrategy(Strategy):
    ticker = None

    def init(self):
        df = pd.DataFrame({
            'Open': self.data.Open, 'High': self.data.High,
            'Low': self.data.Low, 'Close': self.data.Close,
            'Volume': self.data.Volume
        })
        self.signals = self.I(lambda: analyze_stock(df, self.ticker)['Signal_Score'], name="Signal_Score")

    def next(self):
        if self.signals[-1] >= 3:
            if not self.position:
                self.buy()
        elif self.signals[-1] <= 1:
            self.position.close()

def run_backtest(ticker, start_date, end_date):
    """
    Runs a backtest for a given ticker and date range.
    """
    data = yf.download(ticker, start=start_date, end=end_date, interval="1d")
    
    if data.empty:
        return None, None
        
    # --- NEW ROBUST FIX: Force column names to match what backtesting.py expects ---
    # This handles all inconsistencies from yfinance (e.g., 'Adj Close', lowercase, etc.)
    expected_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Ensure we don't try to rename more columns than we have
    num_cols_to_rename = min(len(data.columns), len(expected_cols))
    
    # Create a mapping from the actual column names to the expected ones
    rename_map = {data.columns[i]: expected_cols[i] for i in range(num_cols_to_rename)}
    
    data.rename(columns=rename_map, inplace=True)
    # --------------------------------------------------------------------------
    
    # Check if all required columns are present after renaming
    required_cols = {'Open', 'High', 'Low', 'Close'}
    if not required_cols.issubset(data.columns):
        st.error(f"Downloaded data for {ticker} is missing required columns. Found: {list(data.columns)}")
        return None, None

    bt = Backtest(data, AdvancedStrategy, cash=100000, commission=.002)
    stats, plot = bt.run(ticker=ticker)
    
    return stats, plot
