import ccxt
import os
from typing import List, Dict, Any

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


def initialize_exchanges(exchange_ids: List[str]) -> Dict[str, Any]:

    raise NotImplementedError
    # Fails on Kucoin because password is required
    # May initializes exchanges that only have public methods availabe and therefore can have unexpected behavior

    exchanges = {}

    for exchange_id in exchange_ids:

        api_key = os.environ.get(f"{exchange_id.upper()}_API_KEY")
        secret_key = os.environ.get(f"{exchange_id.upper()}_SECRET_KEY")

        try:
            exchange = (
                getattr(ccxt, exchange_id)({"apiKey": api_key, "secret": secret_key})
                if api_key and secret_key
                else getattr(ccxt, exchange_id)()
            )
            exchanges[exchange_id] = exchange

        except Exception as e:
            print(f"Couldn't initialize exchange {exchange_id}: {e}")

    return exchanges
