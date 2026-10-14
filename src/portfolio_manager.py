"""
portfolio_manager.py
---------------------
Portfolio mein stock add/remove karne aur JSON file mein permanently
save karne ke liye. Isi wajah se browser refresh/restart ke baad bhi
tumhara portfolio yaad rehta hai.
"""

import json
import os

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "mock_portfolio.json")


def load_portfolio_raw() -> dict:
    with open(PORTFOLIO_FILE, "r") as f:
        return json.load(f)


def save_portfolio_raw(data: dict):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_stock(symbol: str, name: str, quantity: float, avg_buy_price: float, buy_date: str, sector: str = "Other"):
    """
    Naya stock portfolio mein add karta hai. Agar symbol already hai,
    toh quantity aur average price update kar deta hai (jaise real
    broker karta hai jab tum same stock dobara khareedte ho).
    """
    data = load_portfolio_raw()
    symbol = symbol.upper().strip()
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol = symbol + ".NS"  # default NSE

    existing = next((h for h in data["holdings"] if h["symbol"] == symbol), None)

    if existing:
        old_qty = existing["quantity"]
        old_price = existing["avg_buy_price"]
        new_qty = old_qty + quantity
        new_avg_price = ((old_qty * old_price) + (quantity * avg_buy_price)) / new_qty
        existing["quantity"] = new_qty
        existing["avg_buy_price"] = round(new_avg_price, 2)
    else:
        data["holdings"].append({
            "symbol": symbol,
            "name": name if name else symbol.replace(".NS", "").replace(".BO", ""),
            "quantity": quantity,
            "avg_buy_price": avg_buy_price,
            "buy_date": buy_date,
            "sector": sector
        })

    save_portfolio_raw(data)
    return True


def remove_stock(symbol: str):
    """
    Portfolio se stock permanently remove karta hai.
    """
    data = load_portfolio_raw()
    data["holdings"] = [h for h in data["holdings"] if h["symbol"] != symbol]
    save_portfolio_raw(data)
    return True


def get_all_symbols() -> list:
    data = load_portfolio_raw()
    return [(h["symbol"], h["name"]) for h in data["holdings"]]
