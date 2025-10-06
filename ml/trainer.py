import yfinance as yf
import pandas as pd
import pandas_ta as ta
import xgboost as xgb
from sklearn.metrics import classification_report
import joblib
from datetime import datetime

# A self-contained list of tickers for the trainer
OMXS30_TICKERS = [
    'ERIC-B.ST', 'ADDT-B.ST', 'SCA-B.ST', 'AZN.ST', 'BOL.ST', 'SAAB-B.ST', 'NDA-SE.ST', 'SKA-B.ST',
    'TEL2-B.ST', 'HM-B.ST', 'TELIA.ST', 'NIBE-B.ST', 'LIFCO-B.ST', 'SHB-A.ST', 'SEB-A.ST', 'ESSITY-B.ST',
    'SWED-A.ST', 'EVO.ST', 'SKF-B.ST', 'INDU-C.ST', 'SAND.ST', 'VOLV-B.ST', 'HEXA-B.ST', 'ABB.ST',
    'ASSA-B.ST', 'EPI-A.ST', 'INVE-B.ST', 'EQT.ST', 'ALFA.ST', 'ATCO-A.ST'
]

def prepare_data(tickers, period="10y"):
    """Downloads data for multiple tickers, creates features, and defines the target."""
    all_data = []
    print(f"Downloading historical data for {len(tickers)} tickers...")
    for ticker in tickers:
        data = yf.Ticker(ticker).history(period=period, interval="1d")
        if not data.empty:
            data['Ticker'] = ticker # Add ticker column for grouping
            all_data.append(data)
    
    if not all_data:
        print("Could not download any data. Exiting.")
        return pd.DataFrame()
        
    combined_data = pd.concat(all_data)
    
    print("Calculating features for each stock...")
    processed_groups = []
    for ticker, group in combined_data.groupby('Ticker'):
        # --- FIX: Apply all indicator calculations individually to this single stock's data ---
        group.ta.sma(length=10, append=True)
        group.ta.sma(length=50, append=True)
        group.ta.macd(fast=12, slow=26, signal=9, append=True)
        group.ta.rsi(length=14, append=True)
        group.ta.obv(append=True)
        group.ta.atr(length=14, append=True)
        group.ta.bbands(length=20, append=True)
        processed_groups.append(group)
    
    # Recombine into one large DataFrame with all indicators calculated
    final_data = pd.concat(processed_groups)
    
    # Define the prediction target
    future_window = 5
    future_return_threshold = 0.03
    
    # Group by ticker again to correctly calculate future returns per stock
    final_data['Future_Price'] = final_data.groupby('Ticker')['Close'].shift(-future_window)
    final_data['Target'] = (final_data['Future_Price'] > final_data['Close'] * (1 + future_return_threshold)).astype(int)
    
    # Clean up data
    final_data = final_data.dropna()
    final_data = final_data.drop(columns=['Dividends', 'Stock Splits', 'Future_Price', 'Ticker'])
    
    return final_data

def train_model(data):
    """Splits data by time, trains an XGBoost model, and evaluates it."""
    features = data.drop(columns=['Target']).select_dtypes(include=['number'])
    target = data['Target']
    
    if features.index.tz is None:
        features.index = features.index.tz_localize('UTC')
        
    split_date = pd.to_datetime("2024-01-01").tz_localize('UTC')
    
    X_train, X_test = features[features.index < split_date], features[features.index >= split_date]
    y_train, y_test = target[target.index < split_date], target[target.index >= split_date]

    if X_train.empty or X_test.empty:
        print("Not enough data to perform a train/test split.")
        return None

    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")
    model = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', use_label_encoder=False, n_estimators=200, max_depth=5)
    model.fit(X_train, y_train)
    
    print("\n--- Model Evaluation on Test Data (2024 onwards) ---")
    preds = model.predict(X_test)
    print(classification_report(y_test, preds, zero_division=0))
    
    return model

if __name__ == '__main__':
    training_data = prepare_data(OMXS30_TICKERS)
    
    if not training_data.empty:
        trained_model = train_model(training_data)
        if trained_model:
            # Ensure the ml directory exists
            import os
            if not os.path.exists('ml'):
                os.makedirs('ml')
            
            model_filename = "ml/xgb_model.joblib"
            joblib.dump(trained_model, model_filename)
            print(f"\nModel trained and saved as '{model_filename}'")
