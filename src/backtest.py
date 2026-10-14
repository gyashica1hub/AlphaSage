"""
backtest.py
------------
Model evaluation aur simple backtesting.

Kya karta hai:
1. Model ki accuracy measure karta hai (RMSE, MAE) - ek holdout test
   set pe (data ka last 20% jo model ne training mein nahi dekha)
2. Ek simple trading strategy backtest karta hai: "jab model up predict
   kare, tab hold karo; jab down predict kare, cash mein raho" - aur
   compare karta hai ki ye strategy plain buy-and-hold se better hai
   ya nahi.

Interview mein bolna: "Sirf model banana kaafi nahi hai - maine uski
predictive accuracy bhi validate ki hai ek proper train/test split ke
saath, jaise real ML pipeline mein hota hai."
"""

import numpy as np
import pandas as pd


def evaluate_and_backtest(df: pd.DataFrame, model, scaler, lookback: int = 10, test_fraction: float = 0.2) -> dict:
    """
    df: pura historical data (Close column ke saath)
    model, scaler: trained LSTM model aur uska scaler
    test_fraction: kitna data test/backtest ke liye rakhna hai (default 20%)
    """
    close = df["Close"].values
    n = len(close)
    split = max(lookback, int(n * (1 - test_fraction)))

    if split >= n - 1:
        return None  # Not enough data to backtest

    scaled = scaler.transform(close.reshape(-1, 1)).flatten()

    actuals, predicteds, dates = [], [], []
    has_date = "Date" in df.columns

    for i in range(split, n):
        window = scaled[i - lookback:i].reshape(1, lookback, 1)
        pred_scaled = model.predict(window, verbose=0)[0][0]
        pred_price = scaler.inverse_transform([[pred_scaled]])[0][0]
        actuals.append(float(close[i]))
        predicteds.append(float(pred_price))
        if has_date:
            dates.append(df["Date"].iloc[i])

    actuals_arr = np.array(actuals)
    predicteds_arr = np.array(predicteds)

    rmse = float(np.sqrt(np.mean((actuals_arr - predicteds_arr) ** 2)))
    mae = float(np.mean(np.abs(actuals_arr - predicteds_arr)))

    # Simple backtest: agar predicted price > previous actual price, "buy" (hold for 1 day)
    strategy_returns = []
    for j in range(1, len(actuals)):
        prev_actual = actuals[j - 1]
        predicted_up = predicteds[j] > prev_actual
        actual_return = (actuals[j] - actuals[j - 1]) / actuals[j - 1]
        strategy_returns.append(actual_return if predicted_up else 0.0)

    strategy_cumulative_pct = round((np.prod([1 + r for r in strategy_returns]) - 1) * 100, 2) if strategy_returns else 0.0
    buy_hold_pct = round(((actuals[-1] - actuals[0]) / actuals[0]) * 100, 2) if len(actuals) > 1 else 0.0

    return {
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "test_points": len(actuals),
        "dates": dates if has_date else list(range(len(actuals))),
        "actual": actuals,
        "predicted": predicteds,
        "strategy_return_pct": strategy_cumulative_pct,
        "buy_hold_return_pct": buy_hold_pct,
    }
