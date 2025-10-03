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
        
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(0)
    
    expected_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    num_cols_to_rename = min(len(data.columns), len(expected_cols))
    rename_map = {data.columns[i]: expected_cols[i] for i in range(num_cols_to_rename)}
    data.rename(columns=rename_map, inplace=True)
    
    # --- FIX: Raise a ValueError instead of calling st.error ---
    required_cols = {'Open', 'High', 'Low', 'Close'}
    if not required_cols.issubset(data.columns):
        # This error will be caught by the main dashboard file
        raise ValueError(f"Downloaded data for {ticker} is missing required columns. Found: {list(data.columns)}")

    bt = Backtest(data, AdvancedStrategy, cash=100000, commission=.002)
    stats, plot = bt.run(ticker=ticker)
    
    return stats, plot
