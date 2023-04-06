from router import PathOptimizer
from exchanges import exchanges

if __name__ == "__main__":

    # initiation
    path_optimizer = PathOptimizer(exchanges=exchanges)
    path_optimizer.init_currency_info()

    # initiation with extra params
    path_optimizer = PathOptimizer(
        exchanges=exchanges,
        path_length=10,
        simulated_bal=simulated_bal,
        interex_trading_size=2000,
        min_trading_limit=100,
    )
    path_optimizer.init_currency_info()

    # usage
    path_optimizer.find_arbitrage()
