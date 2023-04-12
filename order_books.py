import os, time
from itertools import permutations, product, combinations
import ccxt
import traceback
from typing import List, Dict, Tuple, Union
import tokens
import exchanges


class OrderBooks:

    """
    A class for fetching order books across multiple exchanges.

    """

    def __init__(self) -> None:

        """ """

        # define attributes here for mutability
        self.symbols = tokens.symbols
        self.exchanges = exchanges.exchanges

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


if __name__ == "__main__":

    order_books = OrderBooks()
    print(order_books.fetch_orderbooks())
