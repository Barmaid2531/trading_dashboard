from backtesting import Backtest, Strategy
import yfinance as yf
import pandas as pd
from strategies.advanced_analyzer import analyze_stock

class AdvancedStrategy(Strategy):
    def init(self):
        # Create a DataFrame compatible with the analyzer
        df = pd.DataFrame({
            'Open': self.data.Open,
            'High': self.data.High,
            'Low': self.data.Low,
            'Close': self.data.Close,
            'Volume': self.data.Volume
        })
        # Pre-calculate all indicators
        self.signals = self.I(lambda: analyze_stock(df)['Signal_Score'], name="Signal_Score")

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
        
    # --- FIX: Flatten MultiIndex columns from yfinance ---
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(0)
        
    bt = Backtest(data, AdvancedStrategy, cash=100000, commission=.002)
    stats = bt.run()
    plot = bt.plot()
    
    return stats, plot
