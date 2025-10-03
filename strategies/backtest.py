# backtest.py

from backtesting import Backtest, Strategy
from data.fetchers.yahoo_fetcher import fetch
from strategies.advanced_analyzer import analyze_stock
import yfinance as yf

# 1. Define the Strategy for the backtesting library
class AdvancedStrategy(Strategy):
    def init(self):
        # Pre-calculate all indicators using our advanced_analyzer function
        self.signals = self.I(lambda x: analyze_stock(pd.DataFrame(x, columns=['Open','High','Low','Close','Volume']))['Signal_Score'], self.data)

    def next(self):
        # Logic for entering a trade
        if self.signals[-1] >= 3: # If Signal Score is "Strong Buy"
            if not self.position:
                self.buy()
        
        # Logic for exiting a trade
        elif self.signals[-1] <= 1: # If Signal Score is "Neutral/Sell"
            self.position.close()

# 2. Create a function to run the backtest
def run_backtest(ticker, start_date, end_date):
    """
    Runs a backtest for a given ticker and date range.
    """
    # Fetch historical daily data for the backtest
    data = yf.download(ticker, start=start_date, end=end_date, interval="1d")
    
    if data.empty:
        return None, None
        
    # Configure and run the backtest
    bt = Backtest(data, AdvancedStrategy, cash=100000, commission=.002)
    stats = bt.run()
    plot = bt.plot()
    
    return stats, plot
