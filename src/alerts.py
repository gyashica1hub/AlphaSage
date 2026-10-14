"""
alerts.py
---------
Stock jab bahut zyada profit ya loss mein chala jaye, uske liye
alert/notification generate karta hai. Thresholds customizable hain
(dashboard sidebar se change kar sakte ho).
"""


def check_alerts(portfolio: list, loss_threshold: float = -10.0, gain_threshold: float = 15.0) -> list:
    """
    Har stock ka P&L % check karta hai aur agar threshold cross ho
    gaya ho toh alert dict return karta hai.

    loss_threshold: negative number, e.g. -10 matlab 10% se zyada loss
    gain_threshold: positive number, e.g. 15 matlab 15% se zyada gain
    """
    alerts = []
    for stock in portfolio:
        pnl_pct = stock.get("pnl_pct", 0)

        # A provider failure is not a loss or gain. Keep the UI usable and
        # let the caller display a data-unavailable state instead.
        if pnl_pct is None:
            continue

        if pnl_pct <= loss_threshold:
            alerts.append({
                "type": "loss",
                "symbol": stock["symbol"],
                "name": stock["name"],
                "pnl_pct": pnl_pct,
                "message": f"{stock['name']} ({stock['symbol']}) is down {abs(pnl_pct)}% from your buy price."
            })
        elif pnl_pct >= gain_threshold:
            alerts.append({
                "type": "gain",
                "symbol": stock["symbol"],
                "name": stock["name"],
                "pnl_pct": pnl_pct,
                "message": f"{stock['name']} ({stock['symbol']}) is up {pnl_pct}% from your buy price."
            })

    return alerts
