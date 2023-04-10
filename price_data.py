import os, time
from itertools import permutations, product, combinations
import ccxt
import traceback
from typing import List, Dict, Tuple, Union


class PriceData:
    def __init__(self, exchange_ids: List[str], symbols: List[str]) -> None:
        """
        A class for fetching ticker data, order books, and finding arbitrage opportunities across multiple exchanges.

        Parameters:
        exchange_ids (List[str]): A list of exchange IDs to use for fetching tickers.
        symbols (List[str]): A list of symbol pairs to fetch tickers for.

        Usage:
        ```
        p = PriceData(exchange_ids = ["kucoin", "phemex"], symbols=["BTC/USDT", "ETH/USDT", "LTC/USDT"])
        tickers = list(p)
        arbitrage_opportunities = p.find_arbitrage()
        orderbooks = p.fetch_orderbooks()
        ```
        """
        self.symbols = symbols
        self.exchanges = {}
        self.exchange_symbols = list(product(exchange_ids, symbols))
        self.current_index = 0

        # Initialize the exchange objects
        for exchange_id in exchange_ids:
            api_key = os.environ.get(f"{exchange_id.upper()}_API_KEY")
            secret_key = os.environ.get(f"{exchange_id.upper()}_SECRET_KEY")

            try:
                exchange = (
                    getattr(ccxt, exchange_id)(
                        {"apiKey": api_key, "secret": secret_key}
                    )
                    if api_key and secret_key
                    else getattr(ccxt, exchange_id)()
                )
                self.exchanges[exchange_id] = exchange
            except Exception as e:
                print(f"Couldn't initialize exchange {exchange_id}: {e}")

    def __iter__(self) -> "PriceData":
        """
        Initialize the iterator object with the current index.
        """
        self.current_index = 0
        return self

    def __next__(self) -> Dict[str, str]:
        """
        Fetch the ticker from the current index and update the index for the next iteration.

        Returns:
        A dictionary containing the current ticker's exchange, symbol, and price.
        """
        try:
            if self.current_index >= len(self.exchange_symbols):
                raise StopIteration

            exchange_id, symbol = self.exchange_symbols[self.current_index]
            exchange = self.exchanges.get(exchange_id)

            if not exchange:
                raise ValueError(f"Exchange not initialized: {exchange_id}")

            ticker = exchange.fetch_ticker(symbol)
            price = ticker["last"]
        except (StopIteration, ValueError) as e:
            raise e
        except Exception as e:
            print(
                f"An error occurred while fetching ticker from {exchange_id} for {symbol}: {e}"
            )
            price = None
        finally:
            self.current_index += 1

        return {"exchange": exchange_id, "symbol": symbol, "price": price}

    def fetch_orderbooks(self, depth: int = 100) -> List[List]:
        """
        Fetches the order books for each symbol on each exchange in the instance's list of exchange IDs.

        Args:
        - depth (int): The number of price levels to fetch from the order book (default=100).

        Returns:
        A list of lists, where each sub-list contains:
        - symbol (str): The symbol for which the order book was fetched.
        - exchange_id (str): The exchange ID from which the order book was fetched.
        - timestamp (int): The current timestamp in milliseconds.
        - order_book (dict): A dictionary containing two lists: "bids" and "asks". Each list contains a list of lists, where the inner lists represent a price level and its corresponding quantity. The prices and quantities are in floating point format.
        """
        orderbooks = []
        for symbol in self.symbols:
            for exchange_id, exchange in self.exchanges.items():
                try:
                    orderbook = exchange.fetch_order_book(symbol, depth)
                    timestamp = int(time.time() * 1000)
                    bids = [
                        [float(price), float(amount)]
                        for price, amount in orderbook["bids"]
                    ]
                    asks = [
                        [float(price), float(amount)]
                        for price, amount in orderbook["asks"]
                    ]
                    orderbooks.append(
                        [symbol, exchange_id, timestamp, {"bids": bids, "asks": asks}]
                    )
                except Exception as e:
                    print(f"Error fetching order book: {e}")
                    continue
        return orderbooks

    def get_reversed_symbols(self) -> List[str]:
        reversed_symbols = []
        for symbol in self.symbols:
            base, quote = symbol.split("/")
            reversed_symbols.append(f"{quote}/{base}")
        return reversed_symbols

    def get_orderbook_price(
        self, orderbook: Dict[str, List], action: str, reversed_pair: bool
    ) -> float:
        if reversed_pair:
            if action == "buy":
                return 1 / orderbook["bids"][0][0]
            elif action == "sell":
                return orderbook["asks"][0][0]
            else:
                raise ValueError("Invalid action. Use 'buy' or 'sell'.")
        else:
            if action == "buy":
                return orderbook["asks"][0][0]
            elif action == "sell":
                return orderbook["bids"][0][0]
            else:
                raise ValueError("Invalid action. Use 'buy' or 'sell'.")

    def get_all_routes(self) -> List[Tuple[str]]:
        unique_currencies = set()
        for symbol in self.symbols:
            base, quote = symbol.split("/")
            unique_currencies.add(base)
            unique_currencies.add(quote)

        valid_routes = []

        for start_currency in unique_currencies:
            for end_currency in unique_currencies:
                if start_currency == end_currency:
                    continue

                for path_length in range(2, len(unique_currencies)):
                    for path in permutations(unique_currencies, path_length):
                        if path[0] == start_currency and path[-1] == end_currency:
                            route_symbols = [
                                f"{path[i]}/{path[i + 1]}" for i in range(len(path) - 1)
                            ]
                            route_symbols.append(f"{end_currency}/{start_currency}")
                            if all(
                                [
                                    symbol in self.symbols
                                    or f"{symbol.split('/')[1]}/{symbol.split('/')[0]}"
                                    in self.symbols
                                    for symbol in route_symbols
                                ]
                            ):
                                valid_routes.append(tuple(route_symbols))

        return valid_routes

    def is_reversed_pair(self, symbol: str, exchange_id: str) -> bool:
        return (
            symbol not in self.exchanges[exchange_id].symbols
            and f"{symbol.split('/')[1]}/{symbol.split('/')[0]}"
            in self.exchanges[exchange_id].symbols
        )


if __name__ == "__main__":
    try:
        p = PriceData(
            exchange_ids=["kucoin", "phemex"],
            symbols=[
                "BTC/USDT",
                "ETH/USDT",
                "LTC/USDT",
                "BTC/USDC",
                "ETH/USDC",
                "LTC/USDC",
                "BTC/ETH",
            ],
        )
        print(p.get_all_routes())

    except Exception as e:
        print(f"An error occurred: {e}")
        print(traceback.format_exc())
    # symbols = (
    #     [
    #         "BTC/USDT",
    #         "USDT/BTC",
    #         "ETH/USDT",
    #         "USDT/ETH",
    #         "LTC/USDT",
    #         "USDT/LTC",
    #         "BNB/USDT",
    #         "USDT/BNB",
    #         "DOGE/USDT",
    #         "USDT/DOGE",
    #         "ADA/USDT",
    #         "USDT/ADA",
    #         "XRP/USDT",
    #         "USDT/XRP",
    #         "BTC/USDC",
    #         "USDC/BTC",
    #         "ETH/USDC",
    #         "USDC/ETH",
    #         "LTC/USDC",
    #         "USDC/LTC",
    #         "BNB/USDC",
    #         "USDC/BNB",
    #         "DOGE/USDC",
    #         "USDC/DOGE",
    #         "ADA/USDC",
    #         "USDC/ADA",
    #         "XRP/USDC",
    #         "USDC/XRP",
    #         "USDC/USDT",
    #         "USDT/USDC",
    #     ],
    # )
