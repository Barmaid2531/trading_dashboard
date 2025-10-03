# ml_trainer.py
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# --- 1. Data Preparation ---
def prepare_data(ticker, period="10y"):
    """Downloads data, creates features, and defines the prediction target."""
    data = yf.Ticker(ticker).history(period=period, interval="1d")
    
    # Feature Engineering: Calculate indicators
    data.ta.strategy("All", sma_fast=10, sma_slow=50, macd_fast=12, macd_slow=26, macd_signal=9, rsi_length=14, obv=True)
    
    # Target Label Creation: Predict if the price will rise by 3% within the next 5 days
    future_window = 5
    future_return_threshold = 0.03 # 3%
    
    data['Future_Price'] = data['Close'].shift(-future_window)
    data['Target'] = (data['Future_Price'] > data['Close'] * (1 + future_return_threshold)).astype(int)
    
    # Clean up data
    data = data.dropna()
    data = data.drop(columns=['Dividends', 'Stock Splits', 'Future_Price'])
    
    return data

# --- 2. Model Training ---
def train_model(data):
    """Splits data, trains an XGBoost model, and evaluates it."""
    features = data.drop(columns=['Target'])
    target = data['Target']
    
    # Ensure all feature columns are numeric
    features = features.select_dtypes(include=['number'])
    
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
    
    print("Training XGBoost model...")
    model = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', use_label_encoder=False)
    model.fit(X_train, y_train)
    
    # --- 3. Evaluation ---
    print("\n--- Model Evaluation ---")
    preds = model.predict(X_test)
    print(classification_report(y_test, preds))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, preds))
    
    return model

if __name__ == '__main__':
    # Choose a ticker with a long history for training
    training_ticker = "VOLV-B.ST"
    print(f"Preparing data for {training_ticker}...")
    training_data = prepare_data(training_ticker)
    
    if not training_data.empty:
        trained_model = train_model(training_data)
        
        # --- 4. Save the Model ---
        model_filename = "xgb_model.joblib"
        joblib.dump(trained_model, model_filename)
        print(f"\nModel trained and saved as '{model_filename}'")
