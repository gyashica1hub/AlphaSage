"""
predict.py
----------
Stock price prediction module.

Do approaches diye hain:
1. simple_moving_average_prediction() - fast, no training needed, tez chalta hai
2. lstm_predict() - Deep Learning based (LSTM), yeh "DL" wala core hissa hai
   jo resume/interview mein highlight karna hai.

LSTM training ko AWS SageMaker training job mein migrate karna easy hai -
bas train_lstm() ko SageMaker entry-point script bana do (comments mein
bataya hai kaise).
"""

import numpy as np
import pandas as pd
import os
import joblib

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# TensorFlow import - agar install nahi hai to graceful fallback
try:
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from sklearn.preprocessing import MinMaxScaler
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


def _model_paths(symbol: str):
    """Har stock ke liye alag model file - symbol ke dots hatakar safe filename banate hain."""
    safe = symbol.replace(".", "_")
    model_path = os.path.join(MODEL_DIR, f"{safe}_lstm.keras")
    scaler_path = os.path.join(MODEL_DIR, f"{safe}_scaler.pkl")
    return model_path, scaler_path


def load_saved_model(symbol: str):
    """
    Pehle se trained model disk se load karta hai (agar exist karta hai).
    Isse har dashboard refresh pe retrain nahi karna padta - production
    systems bhi isi tarah kaam karte hain (train once, serve many times).
    """
    if not TF_AVAILABLE:
        return None, None
    model_path, scaler_path = _model_paths(symbol)
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        try:
            model = load_model(model_path)
            scaler = joblib.load(scaler_path)
            return model, scaler
        except Exception as e:
            print(f"[predict] Failed to load saved model for {symbol}: {e}")
    return None, None


def train_and_save(symbol: str, df: pd.DataFrame, lookback: int = 10, epochs: int = 20):
    """
    Model train karke disk pe save karta hai, taaki agli baar dobara
    train na karna pade. Yehi asli "training pipeline" hai jo interview
    mein bata sakti ho - SageMaker training job mein isi logic ko
    directly migrate kiya ja sakta hai.
    """
    model, scaler, lb = train_lstm(df, lookback, epochs)
    if model is not None:
        model_path, scaler_path = _model_paths(symbol)
        model.save(model_path)
        joblib.dump(scaler, scaler_path)
    return model, scaler, lb


def simple_moving_average_prediction(df: pd.DataFrame, window: int = 5) -> float:
    """
    Fallback / baseline prediction - LSTM ke bina bhi kaam chale.
    """
    if df.empty or len(df) < window:
        return None
    return round(df["Close"].tail(window).mean(), 2)


def prepare_lstm_data(df: pd.DataFrame, lookback: int = 10):
    """
    Time-series data ko LSTM ke liye (samples, timesteps, features) shape mein convert karta hai.
    """
    scaler = MinMaxScaler(feature_range=(0, 1))
    close_prices = df["Close"].values.reshape(-1, 1)
    scaled = scaler.fit_transform(close_prices)

    X, y = [], []
    for i in range(lookback, len(scaled)):
        X.append(scaled[i - lookback:i, 0])
        y.append(scaled[i, 0])

    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    return X, y, scaler


def build_lstm_model(lookback: int = 10):
    """
    LSTM architecture - interview mein isko explain karna:
    - 2 LSTM layers (64, 32 units) - temporal patterns capture karte hain
    - Dropout - overfitting rokne ke liye
    - Dense output layer - single value (next price) predict karta hai
    """
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(lookback, 1)),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(16, activation="relu"),
        Dense(1)
    ])
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


def train_lstm(df: pd.DataFrame, lookback: int = 10, epochs: int = 20):
    """
    LSTM ko historical data pe train karta hai.

    ---- AWS SageMaker migration note ----
    Production mein isko SageMaker training job banane ke liye:
    1. Is function ko `train.py` entry point mein daalo
    2. sagemaker.tensorflow.TensorFlow estimator use karo:
         estimator = TensorFlow(entry_point='train.py', instance_type='ml.m5.large', ...)
    3. estimator.fit({'training': s3_data_path})
    Interview mein yeh explain karna important hai - "training pipeline
    SageMaker-compatible design kiya hai, containerized aur scalable".
    """
    if not TF_AVAILABLE:
        raise ImportError("TensorFlow/sklearn install karo: pip install tensorflow scikit-learn")

    X, y, scaler = prepare_lstm_data(df, lookback)
    if len(X) < 5:
        return None, None, None

    model = build_lstm_model(lookback)
    model.fit(X, y, epochs=epochs, batch_size=16, verbose=0)
    return model, scaler, lookback


def lstm_predict_next(df: pd.DataFrame, model, scaler, lookback: int = 10) -> float:
    """
    Trained model se next price predict karta hai.
    """
    last_sequence = df["Close"].values[-lookback:].reshape(-1, 1)
    scaled_seq = scaler.transform(last_sequence)
    X_input = np.reshape(scaled_seq, (1, lookback, 1))

    pred_scaled = model.predict(X_input, verbose=0)
    pred_price = scaler.inverse_transform(pred_scaled)
    return round(float(pred_price[0][0]), 2)


def get_prediction(df: pd.DataFrame, symbol: str = None) -> dict:
    """
    Master function - dashboard yehi call karega.
    Pehle saved model try karta hai (fast). Agar nahi milta, LSTM train
    karke save karta hai. Fail ho toh moving average pe fallback.
    """
    current_price = round(df["Close"].iloc[-1], 2) if not df.empty else None

    if TF_AVAILABLE and len(df) > 30:
        try:
            model, scaler = (None, None)
            lookback = 10

            if symbol:
                model, scaler = load_saved_model(symbol)

            if model is None:
                if symbol:
                    model, scaler, lookback = train_and_save(symbol, df)
                else:
                    model, scaler, lookback = train_lstm(df)

            if model:
                predicted = lstm_predict_next(df, model, scaler, lookback)
                method = "LSTM (Deep Learning) - saved model" if symbol and os.path.exists(_model_paths(symbol)[0]) else "LSTM (Deep Learning) - freshly trained"
            else:
                predicted = simple_moving_average_prediction(df)
                method = "Moving Average (fallback - not enough data for LSTM)"
        except Exception as e:
            print(f"[predict] LSTM failed: {e}")
            predicted = simple_moving_average_prediction(df)
            method = "Moving Average (fallback - LSTM error)"
    else:
        predicted = simple_moving_average_prediction(df)
        method = "Moving Average (TensorFlow not installed or insufficient data)"

    trend = None
    if predicted and current_price:
        trend = "Up" if predicted > current_price else "Down"

    return {
        "current_price": current_price,
        "predicted_price": predicted,
        "trend": trend,
        "method": method
    }
