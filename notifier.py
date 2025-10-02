import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import pandas as pd

# Reuse our existing functions
from ui.dashboard import get_omxs30_tickers
from data.fetchers.yahoo_fetcher import fetch
from strategies.moving_average import generate_signals

# --- Email Configuration ---
# For security, use environment variables for your email and password.
# Do NOT write your password directly in the code.
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('APP_PASSWORD') # Use an "App Password" for Gmail
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')

def send_notification(ticker, price, signal_time):
    """Sends an email notification for a strong buy signal."""
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL]):
        print("Email credentials not set. Skipping notification.")
        return

    subject = f"🚀 Strong Buy Alert: {ticker}"
    body = f"""
    A strong buy signal was detected for {ticker}.

    - **Time:** {signal_time.strftime('%Y-%m-%d %H:%M')}
    - **Price:** {price:.2f} SEK

    This alert was triggered by a short-term moving average crossover.
    """

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    try:
        print(f"Connecting to SMTP server to send alert for {ticker}...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print("Notification sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def check_for_strong_buys():
    """Main function to check all stocks and send notifications."""
    print("Starting analysis run...")
    tickers = get_omxs30_tickers()
    now = datetime.now(pd.Timestamp.now().tz) # Get timezone-aware current time

    for ticker in tickers:
        try:
            data = fetch(ticker)
            if data.empty:
                continue
            
            strategy_data = generate_signals(data)
            
            # A "strong" signal is a buy crossover that happened very recently.
            # We look for a 'Position' change of 2 within the last 10 minutes.
            time_filter = now - timedelta(minutes=10)
            recent_buys = strategy_data[(strategy_data['Position'] == 2) & (strategy_data.index >= time_filter)]

            if not recent_buys.empty:
                # Get the most recent buy signal
                latest_buy = recent_buys.iloc[-1]
                price = latest_buy['Close']
                signal_time = latest_buy.name # The index is the timestamp
                
                print(f"Strong buy signal found for {ticker} at {signal_time}!")
                send_notification(ticker, price, signal_time)

        except Exception as e:
            print(f"Could not analyze {ticker}. Error: {e}")
    
    print("Analysis run finished.")

if __name__ == "__main__":
    check_for_strong_buys()
