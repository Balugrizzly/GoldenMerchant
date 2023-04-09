import os
import itertools
import ccxt
import traceback
from typing import List, Dict, Any
import math


class PriceDataGraph:
    def __init__(
        self, exchange_ids: List[str], symbols: List[str], n_best: int = 1
    ) -> None:
        """
        Initialize the PriceDataGraph object with a list of exchange IDs, a list of symbols, and the number of best trades.

        Parameters:
        exchange_ids (List[str]): A list of exchange IDs to use for fetching tickers.
        symbols (List[str]): A list of symbol pairs to fetch tickers for.
        n_best (int): The number of best trades to consider from the orderbook.
        """
        self.symbols = symbols
        self.exchanges = {}
        self.exchange_symbols = list(itertools.product(exchange_ids, symbols))
        self.n_best = n_best

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

        self.graph = self.build_graph(n_best=n_best)

    def build_graph(
        self, n_best: int, transaction_fee: float = 0.0, slippage: float = 0.0
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Build the graph network representing the best orderbook prices and quantities, factoring in transaction fees and slippage,
        consolidating the top N orderbook entries for each symbol into a single entry, and using the specified value of N.

        Parameters:
        n_best (int): The number of top bids and asks to consider for each symbol.
        transaction_fee (float): The percentage transaction fee to apply to each trade.
        slippage (float): The maximum percentage slippage to allow for each trade.

        Returns:
        A nested dictionary representing the graph network.
        """
        graph = {}

        for exchange_id, symbol in self.exchange_symbols:
            exchange = self.exchanges.get(exchange_id)

            if not exchange:
                print(f"Exchange not initialized: {exchange_id}")
                continue

            try:
                orderbook = exchange.fetch_order_book(symbol)
                bids = orderbook["bids"][:n_best]
                asks = orderbook["asks"][:n_best]

                base, quote = symbol.split("/")

                # Calculate weighted average bid and ask prices
                bid_price = sum([bid[0] * bid[1] for bid in bids]) / sum(
                    [bid[1] for bid in bids]
                )
                ask_price = sum([ask[0] * ask[1] for ask in asks]) / sum(
                    [ask[1] for ask in asks]
                )

                # Factor in transaction fee and slippage
                bid_price *= 1 + transaction_fee
                bid_price *= 1 - slippage
                ask_price *= 1 - transaction_fee
                ask_price *= 1 + slippage

                # Calculate total bid and ask volumes
                bid_volume = sum([bid[1] for bid in bids])
                ask_volume = sum([ask[1] for ask in asks])

                if base not in graph:
                    graph[base] = {}
                if quote not in graph:
                    graph[quote] = {}

                # Add consolidated bid and ask to graph
                if quote not in graph[base]:
                    graph[base][quote] = []
                if base not in graph[quote]:
                    graph[quote][base] = []

                graph[base][quote].append(
                    {
                        "exchange": exchange_id,
                        "rate": -math.log(bid_price),
                        "amount": bid_volume,
                        "type": "bid",
                        "price": bid_price,
                    }
                )
                graph[quote][base].append(
                    {
                        "exchange": exchange_id,
                        "rate": math.log(ask_price),
                        "amount": ask_volume,
                        "type": "ask",
                        "price": ask_price,
                    }
                )

            except Exception as e:
                print(
                    f"An error occurred while fetching orderbook from {exchange_id} for {symbol}: {e}"
                )

        return graph

    def find_cyclic_paths(
        self, start_currency: str, max_depth: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """
        Find all cyclic paths in the graph starting and ending with the specified currency.

        Parameters:
        start_currency (str): The starting and ending currency for the cyclic path.
        max_depth (int): The maximum number of intermediate currencies allowed in a path.

        Returns:
        A list of cyclic paths, with each path represented as a list of dictionaries containing trade information.
        """

        def dfs(currency, current_path, depth):
            if depth == 0:
                return

            for next_currency, trades in self.graph[currency].items():
                for trade in trades:
                    trade_with_currencies = {
                        "source_currency": currency,
                        "destination_currency": next_currency,
                        **trade,
                    }
                    if next_currency == start_currency:
                        paths.append(current_path + [trade_with_currencies])
                    elif next_currency not in visited:
                        visited.add(next_currency)
                        dfs(
                            next_currency,
                            current_path + [trade_with_currencies],
                            depth - 1,
                        )
                        visited.remove(next_currency)

        paths = []
        visited = set([start_currency])
        dfs(start_currency, [], max_depth)
        return paths


if __name__ == "__main__":
    symbols = ["BTC/USDT", "ETH/USDT", "LTC/USDT", "ETH/BTC"]
    exchange_ids = ["kucoin", "phemex"]
    n_best = 25
    transaction_fee = 0.0
    slippage = 0.0

    price_data_graph = PriceDataGraph(exchange_ids, symbols, n_best)
    print("Graph")
    print(price_data_graph.graph)

    start_currency = "USDT"
    max_depth = 5
    cyclic_paths = price_data_graph.find_cyclic_paths(start_currency, max_depth)
    print("Cyclic Paths")
    for path in cyclic_paths:
        print("Path")
        print("Base currency:", start_currency)
        for trade in path:
            print(trade)
