from datetime import datetime
from decimal import Decimal
import json
import uuid


class Order(object):

    def __init__(self, quote):
        self.order_id = str(uuid.uuid4())
        self.account_id = quote["account_id"]
        self.side = quote["side"]
        self.order_type = quote["order_type"]
        self.symbol = quote["symbol"]
        self.price = None
        if self.order_type == "LIMIT":
            self.price = quote["price"]
        self.timestamp = datetime.now()
        self.initial_quantity = quote["quantity"]
        self.quantity = quote["quantity"]
        self.trades = []

    def json(self):
        response = {
            "order_id": self.order_id,
            "account_id": self.account_id,
            "side": self.side,
            "order_type": self.order_type,
            "symbol": self.symbol,
            "price": str(self.price),
            "timestamp": str(self.timestamp),
            "initial_quantity": str(self.initial_quantity),
            "quantity": str(self.quantity),
            "trades": [str(trades) for trades in self.trades]
        }
        return json.dumps(response)

    def update(self, quantity):
        self.quantity = quantity

    def __repr__(self):
        order_string = f"{self.side} - {self.initial_quantity} {self.symbol} @ MARKET"
        if self.price:
            order_string = f"{self.side} - {self.initial_quantity} {self.symbol} @ {self.price}"
        return order_string

class Trade(object):

    def __init__(self, existing_order, incoming_order, quantity):
        self.trade_id = str(uuid.uuid4())
        self.existing_order = existing_order
        self.incoming_order = incoming_order
        self.timestamp = datetime.now()
        self.price = self.existing_order.price
        self.symbol = self.existing_order.symbol
        self.quantity = quantity

    def json(self):
        response = {
            "trade_id": self.trade_id,
            "buyer": self.existing_order.account_id,
            "seller": self.incoming_order.account_id,
            "buying_order": self.existing_order.order_id,
            "selling_order": self.incoming_order.order_id,
            "symbol": self.symbol,
            "price": str(self.price),
            "timestamp": str(self.timestamp),
            "quantity": str(self.quantity)
        }
        if self.existing_order.side == "BUY":
            response["buyer"] = self.existing_order.account_id,
            response["seller"] = self.incoming_order.account_id,
            response["buying_order"] = self.existing_order.order_id
            response["selling_order"] = self.incoming_order.order_id
        else:
            response["buyer"] = self.incoming_order.account_id,
            response["seller"] = self.existing_order.account_id,
            response["buying_order"] = self.incoming_order.order_id
            response["selling_order"] = self.existing_order.order_id
        return json.dumps(response)

    def __repr__(self):
        sender = self.existing_order.account_id
        receiver = self.incoming_order.account_id
        return f"{self.quantity} {self.symbol} @ {self.price}: Accounts {sender} & {receiver}"

class OrderList(object):

    def __init__(self, side, price):
        self.side = side
        self.price = price
        self.orders = []
        self.volume = 0
        self.length = 0

    def __len__(self):
        return self.length

    def remove_partial(self, quantity):
        self.volume -= quantity

    def sort_orders(self):
        self.orders.sort(key=lambda x: x.timestamp)

    def add_order(self, order):
        if self.price == order.price:
            self.orders.append(order)
            self.volume += order.quantity
            self.length += 1
            self.sort_orders()
        else:
            raise PriceError("Incorrect order list for order price.")

    def remove_order(self, order):
        found = False
        for orders in self.orders:
            if order.order_id == orders.order_id:
                self.orders.remove(orders)
                self.volume -= order.quantity
                self.length -= 1
                self.sort_orders()
                found = True
        if not found:
            raise OrderError("This order does not exist in the order list.")

    def __repr__(self):
        return str(self.orders)

class OrderBook(object):

    def __init__(self, symbol):
        self.symbol = symbol
        self.bids = {}
        self.asks = {}
        self.side_mapping = {"BUY": self.bids, "SELL": self.asks}
        self.best_price = {"BUY": self.get_min_ask, "SELL": self.get_max_bid}
        self.type_mapping = {"MARKET": self._process_market_order, "LIMIT": self._process_limit_order}
        self.bid_volume = 0
        self.ask_volume = 0
        self.ongoing_orders = {}

    def get_max_bid(self):
        max_bid = None
        if self.bids:
            max_bid = max(self.bids)
        return max_bid

    def get_min_ask(self):
        min_ask = None
        if self.asks:
            min_ask = min(self.asks)
        return min_ask

    def process_order(self, quote):
        self.completed_orders = {}
        self.completed_trades = {}
        order = None
        if quote["symbol"] == self.symbol:
            order = Order(quote)
            self.ongoing_orders[order.order_id] = order.json()
            self._direct_order(order)
        else:
            raise OrderError("Symbol not correct for this order book.")
        return order.json()

    def cancel_order(self, order_id):
        order = self._get_order_by_id(order_id)
        if order.trades:
            raise OrderError("Order has already been partially filled.")
        else:
            self.side_mapping[order.side][order.price].remove_order(order)
            del self.ongoing_orders[order.order_id]
            self._remove_empty_order_lists()

    def modify_order(self, order_id, quote):
        order = self._get_order_by_id(order_id)
        if order.trades:
            raise OrderError("Order has already been partially filled.")
        else:
            self.cancel_order(order.order_id)
            new_order = self.process_order(quote)
        return new_order

    def _get_order_by_id(self, order_id):
        order = None
        if str(order_id) in list(self.ongoing_orders.keys()):
            order_json = json.loads(self.ongoing_orders[order_id])
            order_list = self.side_mapping[str(order_json["side"])][Decimal(order_json["price"])]
            for orders in order_list.orders:
                if orders.order_id == order_id:
                    order = orders
        if not order:
            raise OrderError("No order with that order ID currently exists.")
        return order

    def _direct_order(self, order):
        self.bid_volume = sum([order_list.volume for order_list in self.bids.values()])
        self.ask_volume = sum([order_list.volume for order_list in self.asks.values()])
        self.type_mapping[order.order_type](order, self.best_price[order.side]())

    def _process_market_order(self, order, best_price):
        order_list = None
        if order.side == "BUY":
            if self.ask_volume >= order.quantity:
                order_list = self.asks[best_price]
        elif order.side == "SELL":
            if self.bid_volume >= order.quantity:
                order_list = self.bids[best_price]
        if best_price and order_list:
            order.price = best_price
            self._process_trades(order, order_list, best_price)
        else:
            raise MarketError("Can not process market order without market.")

    def _process_limit_order(self, order, best_price):
        if best_price:
            if order.side == "BUY" and order.price >= best_price:
                order_list = self.asks[best_price]
                self._process_trades(order, order_list, best_price)
            elif order.side == "SELL" and order.price <= best_price:
                order_list = self.bids[best_price]
                self._process_trades(order, order_list, best_price)
            else:
                self._update_order_book(order)
        else:
            self._update_order_book(order)

    def _process_trades(self, order, order_list, best_price):
        fulfilled_orders = []
        for existing_order in order_list.orders:
            if order.quantity > 0:
                remainder = existing_order.quantity - order.quantity
                if remainder > 0:
                    trade = Trade(existing_order, order, order.quantity)
                    existing_order.update(remainder)
                    order_list.remove_partial(order.quantity)
                    order.update(0)
                    order.trades.append(trade.trade_id)
                    existing_order.trades.append(trade.trade_id)
                    del self.ongoing_orders[order.order_id]
                    self.ongoing_orders[existing_order.order_id] = existing_order.json()
                    self.completed_orders[order.order_id] = order.json()
                elif remainder == 0:
                    trade = Trade(existing_order, order, order.quantity)
                    existing_order.update(0)
                    fulfilled_orders.append(existing_order)
                    order.update(0)
                    order.trades.append(trade.trade_id)
                    existing_order.trades.append(trade.trade_id)
                    del self.ongoing_orders[order.order_id]
                    del self.ongoing_orders[existing_order.order_id]
                    self.completed_orders[order.order_id] = order.json()
                    self.completed_orders[existing_order.order_id] = existing_order.json()
                else:
                    trade = Trade(existing_order, order, existing_order.quantity)
                    existing_order.update(0)
                    fulfilled_orders.append(existing_order)
                    order.update(abs(remainder))
                    order.trades.append(trade.trade_id)
                    existing_order.trades.append(trade.trade_id)
                    del self.ongoing_orders[existing_order.order_id]
                    self.ongoing_orders[order.order_id] = order.json()
                    self.completed_orders[existing_order.order_id] = existing_order.json()
                self.completed_trades[trade.trade_id] = trade.json()
        for orders in fulfilled_orders:
            order_list.remove_order(orders)
        self._remove_empty_order_lists()
        if order.quantity > 0:
            self._direct_order(order)

    def _remove_empty_order_lists(self):
        empty_asks = [key for key, value in self.asks.items() if not value]
        empty_bids = [key for key, value in self.bids.items() if not value]
        for asks in empty_asks:
            del self.asks[asks]
        for bids in empty_bids:
            del self.bids[bids]

    def _update_order_book(self, order):
        order_list = OrderList(order.side, order.price)
        if order.price in self.bids or order.price in self.asks:
            order_list = self.side_mapping[order.side][order.price]
        order_list.add_order(order)
        self.side_mapping[order.side][order.price] = order_list

    def __repr__(self):
        return f"BIDS: {self.bids}\nASKS: {self.asks}"

class Error(Exception):
    pass

class PriceError(Error):
    pass

class OrderError(Error):
    pass

class MarketError(Error):
    pass
