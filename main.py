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

    def get_orderbook_price(self, orderbook: Dict[str, List], action: str) -> float:
        if action == "buy":
            return orderbook["asks"][0][0]
        elif action == "sell":
            return orderbook["bids"][0][0]
        else:
            raise ValueError("Invalid action. Use 'buy' or 'sell'.")

    def get_all_routes(self) -> List[Tuple[str]]:
        all_symbols = self.symbols + self.get_reversed_symbols()
        routes = []
        for symbols_permutation in permutations(all_symbols, len(self.symbols)):
            base, _ = symbols_permutation[0].split("/")
            _, quote = symbols_permutation[-1].split("/")
            if (
                all(
                    symbols_permutation[i] != self.symbols[i]
                    for i in range(len(self.symbols))
                )
                and base == quote
            ):
                routes.append(symbols_permutation)
        return routes

    def calculate_arbitrage_routes(self) -> List[Dict[str, Union[str, float, List]]]:
        orderbooks = self.fetch_orderbooks()
        routes = self.get_all_routes()
        profitable_arbitrage_routes = []

        for route in routes:
            trades = []

            for i, symbol in enumerate(route):
                exchange_id, exchange = next(iter(self.exchanges.items()))

                if symbol not in [o[0] for o in orderbooks if o[1] == exchange_id]:
                    symbol_reversed = f"{symbol.split('/')[1]}/{symbol.split('/')[0]}"
                    reversed_orderbook = [
                        o[3]
                        for o in orderbooks
                        if o[0] == symbol_reversed and o[1] == exchange_id
                    ][0]
                    action = "sell" if i % 2 == 0 else "buy"
                    price, amount = self.get_orderbook_price_and_amount(
                        reversed_orderbook, action
                    )
                    symbol = symbol_reversed
                else:
                    orderbook = [
                        o[3]
                        for o in orderbooks
                        if o[0] == symbol and o[1] == exchange_id
                    ][0]
                    action = "buy" if i % 2 == 0 else "sell"
                    price, amount = self.get_orderbook_price_and_amount(
                        orderbook, action
                    )

                trades.append(
                    {
                        "symbol": symbol,
                        "exchange": exchange_id,
                        "action": action,
                        "price": price,
                        "amount": amount,
                    }
                )

            min_trade_amount = min([trade["amount"] for trade in trades])

            total_profit = min_trade_amount
            for i, trade in enumerate(trades):
                action = trade["action"]
                price = trade["price"]
                total_profit = (
                    total_profit / price if action == "buy" else total_profit * price
                )

            profit = total_profit - min_trade_amount
            currency = route[-1].split("/")[1]

            if profit > 0:
                profitable_arbitrage_routes.append(
                    {
                        "route": route,
                        "profit": f"{profit:.2f} {currency}",
                        "trades": trades,
                    }
                )

        return profitable_arbitrage_routes

    def get_orderbook_price_and_amount(
        self, orderbook: Dict[str, List[Tuple[float, float]]], action: str
    ) -> Tuple[float, float]:
        """
        Get the best price and corresponding amount from the orderbook based on the action (buy or sell).

        Args:
        - orderbook (Dict[str, List[Tuple[float, float]]]): The orderbook containing bids and asks.
        - action (str): The action to be performed, either "buy" or "sell".

        Returns:
        A tuple containing the best price and corresponding amount.
        """
        if action == "buy":
            best_price, amount = orderbook["asks"][0]
        elif action == "sell":
            best_price, amount = orderbook["bids"][0]
        else:
            raise ValueError("Invalid action. Must be 'buy' or 'sell'.")
        return best_price, amount


if __name__ == "__main__":
    try:
        p = PriceData(
            exchange_ids=["kucoin", "phemex"],
            symbols=["BTC/USDT", "ETH/USDT", "LTC/USDT"]
            # symbols=[
            #     "BTC/USDT",
            #     "USDT/BTC",
            #     "ETH/USDT",
            #     "USDT/ETH",
            #     "LTC/USDT",
            #     "USDT/LTC",
            #     "BNB/USDT",
            #     "USDT/BNB",
            #     "DOGE/USDT",
            #     "USDT/DOGE",
            #     "ADA/USDT",
            #     "USDT/ADA",
            #     "XRP/USDT",
            #     "USDT/XRP",
            #     "BTC/USDC",
            #     "USDC/BTC",
            #     "ETH/USDC",
            #     "USDC/ETH",
            #     "LTC/USDC",
            #     "USDC/LTC",
            #     "BNB/USDC",
            #     "USDC/BNB",
            #     "DOGE/USDC",
            #     "USDC/DOGE",
            #     "ADA/USDC",
            #     "USDC/ADA",
            #     "XRP/USDC",
            #     "USDC/XRP",
            #     "USDC/USDT",
            #     "USDT/USDC",
            # ],
        )
        # print(p.get_all_routes())
        x = p.calculate_arbitrage_routes()
        for opp in x:
            print(opp)

    except Exception as e:
        print(f"An error occurred: {e}")
        print(traceback.format_exc())
