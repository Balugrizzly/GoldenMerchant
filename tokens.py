import itertools

tokens = ["BTC", "ETH", "LTC", "USDC", "DAI", "USDT"]


symbols = list(itertools.permutations(tokens, 2))
symbols = ["/".join(symbol) for symbol in symbols]


if __name__ == "__main__":

    print(symbols)
