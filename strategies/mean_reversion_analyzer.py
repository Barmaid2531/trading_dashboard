import pandas as pd
import pandas_ta as ta

def analyze_stock_mean_reversion(data: pd.DataFrame) -> pd.DataFrame:
    """Performs a mean-reversion analysis using Bollinger Bands and RSI."""
    if data.empty or len(data) < 20:
        return pd.DataFrame()

    data.ta.bbands(length=20, append=True)
    data.ta.rsi(length=14, append=True)

    bbl_col = next((col for col in data.columns if col.startswith('BBL_')), 'BBL_20_2.0')
    bbm_col = next((col for col in data.columns if col.startswith('BBM_')), 'BBM_20_2.0')

    conditions = [
        (data['Close'] <= data[bbl_col]) & (data['RSI_14'] < 35),
        (data['Close'] >= data[bbm_col]) & (data['RSI_14'] > 45)
    ]
    choices = ['Buy', 'Sell']
    data['Recommendation'] = pd.Series(pd.NA)
    
    for i in range(len(data)):
        if conditions[0].iloc[i]:
            data.loc[data.index[i], 'Recommendation'] = 'Buy'
        elif conditions[1].iloc[i]:
            data.loc[data.index[i], 'Recommendation'] = 'Sell'
            
    data['Recommendation'].fillna(method='ffill', inplace=True)
    return data
