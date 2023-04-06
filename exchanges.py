import ccxt
import os

exchanges = {
    "kucoin": ccxt.kucoin(
        {
            "apiKey": os.environ.get(f"KUCOIN_API_KEY"),
            "secret": os.environ.get(f"KUCOIN_SECRET_KEY"),
            "password": os.environ.get(f"KUCOIN_API_PASSWORD"),
        }
    ),
    "phemex": ccxt.phemex(
        {
            "apiKey": os.environ.get(f"PHEMEX_API_KEY"),
            "secret": os.environ.get(f"PHEMEX_SECRET_KEY"),
        }
    ),
}
