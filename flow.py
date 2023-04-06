# 1)
#   Get prices from our given exchanges or our given coins(tickers)
#   or all coins(tickers)available
# 1.1)
# This object should take in following:
#     An Exchange Id which should probably be a string and the name of the exchange in lowercase as this mimicks ccxt
#     optionally one or two coins(tickers) params with which we can filter the coins by including or removing those in the param
#     it might make sense to have two coins param a blacklist and a white list
#     the coins parameter is not that crucial and wont affect the behaviour much so we are a bit at liberty there

# The Object should return:
#     a 3 deep nested list:
#     All the coins(tickers) available or specified
#     The exchange_id of the exchange
#     A list of the
#       quantities with corresponding prices for that coin(ticker)
#     [
#         [ticker,exchange_id,timestamp,
#           'bids': [
#               [ price, amount ], // [ float, float ]
#               [ price, amount ],
#               ...
#                   ],
#           'asks': [
#               [ price, amount ],
#               [ price, amount ],
#               ...
#                   ],
#
#
#         [BTC/USDT,kucoin,1499280391811
#             'bids': [
#               [ 28000, 1 ], // [ float, float ]
#               [ 27999, 0.5 ],
#               ...
#                   ],
#              'asks': [
#               [ 29000, 4 ],
#               [ 28100, 6 ],
#               ...
#                       ],
#         ]
#     ]


# 2) Find and filter out Arbitrage oppertunities in the Prices
# 2.1)
# This object should take in the return value of the Price data aka the return value defined previousy above in 1.1
# This object should return the same data structure as it took in and output a filtered version of it


# 3) Router: find a *route for the arbitrage oppertunity
# Take in the Filtered Price data from the Arbitrage object
# *preferably the optimal route but this can be a optimized later and is irrelevant for simple routes i.e from one exchange to another
# Output:

# 4)Fees

# 5)Evaluate
