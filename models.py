import os
import itertools
import ccxt
from typing import List, Dict, Any


class Node:
    def __init__(self, network, exchange, token):
        self.network = network
        self.exchange = exchange
        self.token = token
        self.neighbors = []

    def add_neighbor(self, edge):
        self.neighbors.append(edge)

    def __hash__(self):
        return hash((self.network, self.exchange, self.token))

    def __repr__(self):
        return (
            f"<Node network={self.network} exchange={self.exchange} token={self.token}>"
        )

    def __str__(self):
        return f"{self.network}-{self.exchange}-{self.token}"


class Edge:
    def __init__(self, src_node, dest_node, exchange, amount, price):
        self.src_node = src_node
        self.dest_node = dest_node
        self.exchange = exchange
        self.amount = amount
        self.price = price

    def __repr__(self):
        return (
            f"<Edge src_node={self.src_node} dest_node={self.dest_node} "
            f"exchange={self.exchange} amount={self.amount} price={self.price}>"
        )

    def __str__(self):
        return (
            f"{self.src_node} -> {self.dest_node} | Exchange: {self.exchange} | "
            f"Amount: {self.amount} | Price: {self.price}"
        )


class Graph:
    def __init__(self, edges: List[Edge], nodes: Dict[str, Node]):
        self.edges = edges
        self.nodes = nodes

    def __str__(self):
        result = "Graph Network:\n"
        result += "Nodes:\n"
        for node in self.nodes.values():
            result += f"  {node}:\n"
            result += "  Neighbors:\n"
            for edge in node.neighbors:
                result += f"    {edge}\n"
        return result


def initialize_exchanges(exchange_ids: List[str]) -> Dict[str, Any]:
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


def build_edges(
    exchanges: Dict[str, Any], symbols: List[str], n_best: int
) -> (List[Edge], Dict[str, Node]):
    exchange_symbols = list(itertools.product(exchanges.keys(), symbols))
    edges = []
    nodes = {}

    for exchange_id, symbol in exchange_symbols:
        exchange = exchanges.get(exchange_id)

        if not exchange:
            print(f"Exchange not initialized: {exchange_id}")
            continue

        try:
            orderbook = exchange.fetch_order_book(symbol)
            bids = orderbook["bids"][:n_best]
            asks = orderbook["asks"][:n_best]

            base, quote = symbol.split("/")

            src_key = f"Crypto-{exchange_id}-{base}"
            dest_key = f"Crypto-{exchange_id}-{quote}"

            # TODO: Add support for other networks. For now, we default to mainnet.
            if src_key not in nodes:
                nodes[src_key] = Node("mainnet", exchange_id, base)

            if dest_key not in nodes:
                nodes[dest_key] = Node("mainnet", exchange_id, quote)

            src_node = nodes[src_key]
            dest_node = nodes[dest_key]

            bid_price, bid_volume = calculate_weighted_average_and_volume(bids)
            ask_price, ask_volume = calculate_weighted_average_and_volume(asks)

            bid_edge = Edge(src_node, dest_node, exchange, bid_volume, bid_price)
            ask_edge = Edge(dest_node, src_node, exchange, ask_volume, ask_price)

            src_node.add_neighbor(bid_edge)
            dest_node.add_neighbor(ask_edge)

            edges.append(bid_edge)
            edges.append(ask_edge)

        except Exception as e:
            print(
                f"An error occurred while fetching orderbook from {exchange_id} for {symbol}: {e}"
            )

    return edges, nodes


def calculate_weighted_average_and_volume(
    prices_and_volumes: List[List[float]],
) -> (float, float):
    weighted_average = sum([pv[0] * pv[1] for pv in prices_and_volumes]) / sum(
        [pv[1] for pv in prices_and_volumes]
    )
    volume = sum([pv[1] for pv in prices_and_volumes])
    return weighted_average, volume


if __name__ == "__main__":
    tokens = ["BTC", "ETH", "LTC", "USDC", "DAI", "USDT"]
    symbols = list(itertools.permutations(tokens, 2))
    symbols = ["/".join(symbol) for symbol in symbols]
    exchange_ids = ["kucoin", "phemex"]
    n_best = 25

    exchanges = initialize_exchanges(exchange_ids)
    edges, nodes = build_edges(exchanges, symbols, n_best)

    graph = Graph(edges, nodes)
    print(graph)
