from backtesting import Backtest, Strategy
import pandas as pd
import pandas_ta as ta
from data.fetchers.yfinance_fetcher import fetch_daily_bars
from bokeh.embed import components
from strategies.advanced_analyzer import analyze_stock

# --- Strategy 1: Trend-Following ---
class TrendFollowingStrategy(Strategy):
    ticker = None
    def init(self):
        df = pd.DataFrame({
            'Open': self.data.Open, 
            'High': self.data.High, 
            'Low': self.data.Low, 
            'Close': self.data.Close, 
            'Volume': self.data.Volume
        })
        self.signals = self.I(lambda: analyze_stock(df, self.ticker)['Signal_Score'], name="Signal_Score")

    def next(self):
        if self.signals[-1] >= 5: 
            if not self.position: 
                self.buy()
        elif self.signals[-1] <= 3:
            self.position.close()

# --- Strategy 2: Mean-Reversion ---
class MeanReversionStrategy(Strategy):
    def init(self):
        close_series = pd.Series(self.data.Close)
        self.bbands = self.I(ta.bbands, close_series, length=20, append=False)
        self.rsi = self.I(ta.rsi, close_series, length=14)

    def next(self):
        lower_band = self.bbands.BBL_20_2.0
        middle_band = self.bbands.BBM_20_2.0
        
        if self.data.Close <= lower_band and self.rsi < 35:
            if not self.position: 
                self.buy()
        elif self.data.Close >= middle_band and self.rsi > 55:
            self.position.close()

def run_backtest(ticker, start_date, end_date, strategy_name):
    """
    Runs a backtest for a given ticker, date range, and strategy.
    """
    days = (end_date - start_date).days if end_date > start_date else 365
    data = fetch_daily_bars(ticker, period=f"{days}d")
    data = data[(data.index.date >= start_date) & (data.index.date <= end_date)]
    
    if data.empty or len(data) < 50:
        return None, None, None

    if strategy_name == "Mean-Reversion":
        strategy_to_run = MeanReversionStrategy
    else: 
        strategy_to_run = TrendFollowingStrategy

    bt = Backtest(data, strategy_to_run, cash=100000, commission=.002)
    stats = bt.run(ticker=ticker)
    plot = bt.plot()
    
    if plot:
        script, div = components(plot)
        return stats, script, div
    else:
        return stats, None, None
