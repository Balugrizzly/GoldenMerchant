import os
import itertools
import ccxt
import traceback
from typing import List, Dict


class PriceData:
    def __init__(self, exchange_ids: List[str], symbols: List[str]) -> None:
        """
        Initialize the PriceData object with a list of exchange IDs and a list of symbols.

        Parameters:
        exchange_ids (List[str]): A list of exchange IDs to use for fetching tickers.
        symbols (List[str]): A list of symbol pairs to fetch tickers for.
        """
        self.symbols = symbols
        self.exchanges = {}
        self.exchange_symbols = list(itertools.product(exchange_ids, symbols))
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

    def find_arbitrage(self) -> List[Dict[str, str]]:
        """
        Find all arbitrage opportunities by comparing the current tickers and calculating the profit potential.

        Returns:
        A list of dictionaries containing data on each arbitrage opportunity.
        """
        arbitrage_opportunities = []

        for symbol in self.symbols:
            prices = {}
            for exchange_id, exchange in self.exchanges.items():
                try:
                    ticker = exchange.fetch_ticker(symbol)
                    prices[exchange_id] = ticker["last"]
                except Exception as e:
                    print(
                        f"An error occurred while fetching ticker from {exchange_id} for {symbol}: {e}"
                    )

            # Check if at least two exchanges are available for this symbol
            if len(prices) < 2:
                continue

            # Find the maximum and minimum prices and their corresponding exchange IDs
            min_price_exchange = min(prices, key=prices.get)
            max_price_exchange = max(prices, key=prices.get)

            # Check if the same exchange is used for both minimum and maximum prices
            if min_price_exchange == max_price_exchange:
                continue

            # Calculate the profit potential
            buy_price = prices[min_price_exchange]
            sell_price = prices[max_price_exchange]
            profit = round((sell_price / buy_price - 1) * 100, 2)

            # Add the arbitrage opportunity to the list
            if profit > 0:
                arbitrage_opportunity = {
                    "buy_exchange": min_price_exchange,
                    "buy_symbol": symbol,
                    "buy_price": buy_price,
                    "sell_exchange": max_price_exchange,
                    "sell_symbol": symbol,
                    "sell_price": sell_price,
                    "profit": profit,
                }
                arbitrage_opportunities.append(arbitrage_opportunity)

        return arbitrage_opportunities


if __name__ == "__main__":

    symbols = ["BTC/USDT", "ETH/USDT", "LTC/USDT"]
    exchange_ids = ["kucoin", "phemex"]

    try:
        price_data = PriceData(exchange_ids, symbols)

        # Fetch the current tickers for all exchange/symbol pairs
        for price in price_data:
            if price["price"] is not None:
                print(price)

        # Find any arbitrage opportunities in the current ticker prices
        arbitrage_opportunities = price_data.find_arbitrage()

        # Print the list of arbitrage opportunities
        for opportunity in arbitrage_opportunities:
            print(opportunity)

    except Exception as e:
        print(f"An error occurred: {e}")
        print(traceback.format_exc())
