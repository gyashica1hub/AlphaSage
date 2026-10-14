"""
explainability.py
-------------------
Prediction ko explain karta hai - "kis feature ki wajah se model ne
ye price predict kiya".

Important note: LSTM (deep learning) pe directly SHAP lagana bahut
compute-heavy hota hai. Isliye industry-standard practice follow ki
hai - ek "surrogate model" (Random Forest) train karte hain jo same
features use karke similar prediction deta hai, aur SHAP usi pe lagate
hain. Random Forest par SHAP fast aur reliable hai (TreeExplainer).

Interview mein bolna: "LSTM par directly SHAP compute-expensive hai,
isliye maine ek interpretable surrogate model approach use kiya - ye
real-world explainability pipelines mein common practice hai."
"""

import pandas as pd

try:
    import shap
    from sklearn.ensemble import RandomForestRegressor
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


def build_features(df: pd.DataFrame, sentiment_score: float = 0.0, lookback: int = 5):
    """
    Simple tabular features banata hai: pichle N din ke closing prices
    + sentiment score. Ye surrogate model ke liye input hain.
    """
    close = df["Close"].values
    features, targets = [], []

    for i in range(lookback, len(close)):
        row = list(close[i - lookback:i])
        row.append(sentiment_score)
        features.append(row)
        targets.append(close[i])

    columns = [f"price_{lookback - j}_days_ago" for j in range(lookback)] + ["news_sentiment"]
    X = pd.DataFrame(features, columns=columns)
    y = pd.Series(targets)
    return X, y


def explain_prediction(df: pd.DataFrame, sentiment_score: float = 0.0, lookback: int = 5) -> dict:
    """
    Feature importance return karta hai - dashboard mein bar chart
    ke liye use hoga.
    """
    if not SHAP_AVAILABLE:
        return None

    X, y = build_features(df, sentiment_score, lookback)
    if len(X) < 20:
        return None

    try:
        model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
        model.fit(X, y)

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X.tail(1))

        importance = {col: float(val) for col, val in zip(X.columns, shap_values[0])}
        importance = dict(sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True))
        return importance
    except Exception as e:
        print(f"[explainability] SHAP failed: {e}")
        return None
