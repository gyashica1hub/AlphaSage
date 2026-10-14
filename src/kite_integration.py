"""
kite_integration.py
--------------------
Zerodha Kite Connect se REAL holdings fetch karta hai (free "Personal" plan).

Setup (ek baar karna hai):
1. https://kite.trade pe jaake developer account banao (apne Zerodha login se)
2. "Create new app" -> App type "Personal" (FREE) select karo
3. Redirect URL mein daalo: http://127.0.0.1:5000/callback  (ya kuch bhi, hum manually token generate karenge)
4. API Key aur API Secret milega - .env file mein save karo (neeche dekho)
5. `python src/generate_kite_token.py` ek baar chalao (roz chalana padega, token 1 din valid hota hai)

.env file banao (project root mein), isme:
    KITE_API_KEY=your_api_key_here
    KITE_API_SECRET=your_api_secret_here
    KITE_ACCESS_TOKEN=   (yeh generate_kite_token.py bharega)
"""

import os
from dotenv import load_dotenv

load_dotenv()

KITE_API_KEY = os.getenv("KITE_API_KEY", "")
KITE_API_SECRET = os.getenv("KITE_API_SECRET", "")
KITE_ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN", "")


def is_kite_configured() -> bool:
    """Check karta hai ki Kite credentials set hain ya nahi."""
    return bool(KITE_API_KEY and KITE_ACCESS_TOKEN)


def get_kite_client():
    """Configured KiteConnect client return karta hai."""
    from kiteconnect import KiteConnect
    kite = KiteConnect(api_key=KITE_API_KEY)
    kite.set_access_token(KITE_ACCESS_TOKEN)
    return kite


def fetch_real_holdings() -> list:
    """
    Zerodha se REAL holdings fetch karta hai, aur humare dashboard ke
    format (jaisa mock_portfolio.json mein hai) mein convert karta hai.
    """
    kite = get_kite_client()
    raw_holdings = kite.holdings()

    holdings = []
    for h in raw_holdings:
        holdings.append({
            "symbol": h["tradingsymbol"] + ".NS",   # NSE symbol, yfinance ke liye compatible
            "name": h["tradingsymbol"],
            "quantity": h["quantity"],
            "avg_buy_price": h["average_price"],
            "buy_date": "N/A"  # Kite API buy date directly nahi deta
        })
    return holdings
