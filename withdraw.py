import ccxt
import os

api_key = os.environ.get(f"KUCOIN_API_KEY")
secret_key = os.environ.get(f"KUCOIN_SECRET_KEY")
api_pw = os.environ.get(f"KUCOIN_API_PASSWORD")

kucoin = ccxt.kucoin({"apiKey": api_key, "secret": secret_key, "password": api_pw})

kucoin.withdraw(
    code="MATIC",
    amount=10.0,
    address="0xb14fFDB81E804D2792B6043B90aE5Ac973EcD53D",
    params={"network": "MATIC"},
)
