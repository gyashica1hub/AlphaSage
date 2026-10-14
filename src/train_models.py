"""
train_models.py
-----------------
Standalone training pipeline script. Isko ek baar chalao (ya schedule
karo cron/EventBridge se) taaki saare portfolio stocks ke LSTM models
pre-trained aur disk pe saved rahein. Dashboard phir sirf load karega,
train nahi karega - fast aur production-jaisa.

Chalane ka tarika:
    python src/train_models.py

Interview mein bolna: "Maine training aur serving (inference) ko
separate kiya hai - jaise production ML systems mein hota hai. Ye
architecture SageMaker Training Job + Endpoint pattern se directly
compatible hai."
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.portfolio_manager import load_portfolio_raw
from src.fetch_prices import get_historical_data
from src.predict import train_and_save


def main():
    data = load_portfolio_raw()
    holdings = data["holdings"]

    if not holdings:
        print("Portfolio khali hai - koi stock nahi mila training ke liye.")
        return

    print(f"Training models for {len(holdings)} stocks...\n")

    for stock in holdings:
        symbol = stock["symbol"]
        print(f"[{symbol}] Fetching historical data...")
        df = get_historical_data(symbol, period="1y")

        if df.empty or len(df) < 40:
            print(f"[{symbol}] Skipped - not enough data.\n")
            continue

        print(f"[{symbol}] Training LSTM model...")
        model, scaler, lookback = train_and_save(symbol, df)

        if model:
            print(f"[{symbol}] Model saved successfully.\n")
        else:
            print(f"[{symbol}] Training failed or skipped.\n")

    print("Training pipeline complete. Run 'streamlit run app.py' to use saved models.")


if __name__ == "__main__":
    main()
