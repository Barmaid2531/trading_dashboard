from backtesting import Backtest, Strategy
import yfinance as yf
import pandas as pd
from strategies.advanced_analyzer import analyze_stock

class AdvancedStrategy(Strategy):
    ticker = None  # Add a placeholder for the ticker

    def init(self):
        df = pd.DataFrame({
            'Open': self.data.Open, 'High': self.data.High,
            'Low': self.data.Low, 'Close': self.data.Close,
            'Volume': self.data.Volume
        })
        # Pass the ticker to the analyzer
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
    
    data.rename(columns={
        "open": "Open", "high": "High", "low": "Low", 
        "close": "Close", "volume": "Volume"
    }, inplace=True)
    
    bt = Backtest(data, AdvancedStrategy, cash=100000, commission=.002)
    stats, plot = bt.run(ticker=ticker) # Pass ticker to the run method
    
    return stats, plot
