"""
generate_kite_token.py
------------------------
Yeh script chalao roz (ya jab bhi access token expire ho jaye - Kite ka
token sirf 1 din valid hota hai, security ke liye).

Kaise chalana hai:
    python src/generate_kite_token.py

Yeh ek login URL print karega -> browser mein khol ke apne Zerodha
credentials se login karo -> jis page pe redirect hoga uske URL mein
se "request_token=XXXXX" wala part copy karo -> yahan paste karo jab
script maange.

Access token .env file mein automatically save ho jayega.
"""

import os
import sys
from dotenv import load_dotenv, set_key

load_dotenv()

API_KEY = os.getenv("KITE_API_KEY", "")
API_SECRET = os.getenv("KITE_API_SECRET", "")
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")


def main():
    if not API_KEY or not API_SECRET:
        print("ERROR: .env file mein KITE_API_KEY aur KITE_API_SECRET set karo pehle.")
        sys.exit(1)

    from kiteconnect import KiteConnect
    kite = KiteConnect(api_key=API_KEY)

    login_url = kite.login_url()
    print("\n" + "=" * 70)
    print("STEP 1: Ye URL browser mein kholo aur Zerodha se login karo:")
    print(login_url)
    print("=" * 70)
    print("\nSTEP 2: Login ke baad jis page pe redirect hoga, uske URL mein")
    print("'request_token=XXXXXXXX' dhundo aur sirf wo token yahan paste karo.\n")

    request_token = input("Paste request_token here: ").strip()

    try:
        data = kite.generate_session(request_token, api_secret=API_SECRET)
        access_token = data["access_token"]

        # .env file mein save karo
        if not os.path.exists(ENV_PATH):
            open(ENV_PATH, "a").close()
        set_key(ENV_PATH, "KITE_ACCESS_TOKEN", access_token)

        print("\nSuccess! Access token generate ho gaya aur .env mein save ho gaya.")
        print("Ab 'streamlit run app.py' chalao - real holdings dikhengi.")
        print("(Yaad rakho: ye token sirf aaj ke liye valid hai, kal fir se ye script chalani hogi)")

    except Exception as e:
        print(f"\nError: {e}")
        print("Request token galat ho sakta hai ya expire ho gaya hoga (2 min mein expire hota hai) - dobara try karo.")


if __name__ == "__main__":
    main()
