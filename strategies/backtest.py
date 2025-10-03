from backtesting import Backtest, Strategy
import pandas as pd
from strategies.advanced_analyzer import analyze_stock
from data.fetchers.finnhub_fetcher import fetch_daily_bars
from bokeh.embed import components

class AdvancedStrategy(Strategy):
    ticker = None
    def init(self):
        df = pd.DataFrame({'Open': self.data.Open, 'High': self.data.High, 'Low': self.data.Low, 'Close': self.data.Close, 'Volume': self.data.Volume})
        self.signals = self.I(lambda: analyze_stock(df, self.ticker)['Signal_Score'], name="Signal_Score")
    def next(self):
        if self.signals[-1] >= 4:
            if not self.position: self.buy()
        elif self.signals[-1] <= 2:
            self.position.close()

def run_backtest(ticker, start_date, end_date):
    """Runs a backtest for a given ticker and date range using Finnhub data."""
    days = (end_date - start_date).days
    data = fetch_daily_bars(ticker, days=days)
    data = data[(data.index >= pd.to_datetime(start_date)) & (data.index <= pd.to_datetime(end_date))]
    
    if data.empty or len(data) < 50:
        return None, None, None

    bt = Backtest(data, AdvancedStrategy, cash=100000, commission=.002)
    stats = bt.run(ticker=ticker)
    plot = bt.plot()
    
    if plot:
        script, div = components(plot)
        return stats, script, div
    else:
        return stats, None, None
