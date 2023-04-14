import networkx as nx
from order_books import OrderBooks


class Graph:
    def __init__(self, **kwargs):
        super(self).__init__()

        self.graph = nx.Graph()

    def create_nodes(self):

        order_books = OrderBooks()

        for symbol_exchange_sub_list in order_books.fetch_orderbooks():

            tickers = symbol_exchange_sub_list[0].split("/", 1)
            exchange_id = symbol_exchange_sub_list[1]

            self.graph.add_node(f"{tickers[0]}-{exchange_id}", network=None)
            self.graph.add_node(f"{tickers[1]}-{exchange_id}", network=None)
