from decimal import Decimal
import json
import requests
import unittest

from orderbook import Order, OrderList, OrderBook, Trade


with open("test_quotes.json") as f:
	test_quotes = json.load(f)

class test_order(unittest.TestCase):

	def setUp(self):
		self.order = Order(test_quotes[str(1)])
		self.order2 = Order(test_quotes[str(7)])

	def test_add_order(self):
		self.assertEqual(self.order.price, 100.00)
		self.assertEqual(self.order.side, "BUY")
		self.assertEqual(self.order.type, 'LIMIT')
		self.assertEqual(self.order.symbol, 'KEQ')
		self.assertEqual(self.order.quantity, 50)
		self.assertEqual(self.order.account_id, "1")
		self.assertEqual(self.order2.price, None)
		self.assertEqual(self.order2.side, "BUY")
		self.assertEqual(self.order2.type, 'MARKET')
		self.assertEqual(self.order2.symbol, 'KEQ')
		self.assertEqual(self.order2.quantity, 100)
		self.assertEqual(self.order2.account_id, "7")

	def test_update_order(self):
		self.order.update(75)
		self.assertEqual(self.order.quantity, 75)

class test_trade(unittest.TestCase):

	def setUp(self):
		self.order = Order(test_quotes[str(4)])
		self.order2 = Order(test_quotes[str(5)])
		self.trade = Trade(self.order, self.order2, 75)

	def test_add_order(self):
		self.assertEqual(self.trade.existing_order, self.order)
		self.assertEqual(self.trade.incoming_order, self.order2)
		self.assertEqual(self.trade.price, self.order.price)
		self.assertEqual(self.trade.symbol, 'KEQ')
		self.assertEqual(self.trade.quantity, 75)

class test_order_list(unittest.TestCase):

	def setUp(self):
		self.orders = []
		for i in range(1, 5):
			self.orders.append(Order(test_quotes[str(i)]))
		self.buyOrderList = OrderList("BUY", self.orders[0].price)
		self.sellOrderList = OrderList("SELL", self.orders[1].price)
		self.buyOrderList.add_order(self.orders[0])
		self.sellOrderList.add_order(self.orders[1])
		self.buyOrderList.add_order(self.orders[2])
		self.sellOrderList.add_order(self.orders[3])

	def test_add_order(self):
		self.assertEqual(len(self.buyOrderList), 2)
		self.assertEqual(len(self.sellOrderList), 2)
		self.assertTrue(self.buyOrderList.orders[0].timestamp < self.buyOrderList.orders[1].timestamp)
		self.assertEqual(self.buyOrderList.volume, 150)
		self.assertEqual(self.sellOrderList.volume, 125)

	def test_remove_order(self):
		self.buyOrderList.remove_order(self.orders[0])
		self.sellOrderList.remove_order(self.orders[1])
		self.assertEqual(len(self.buyOrderList), 1)
		self.assertEqual(len(self.sellOrderList), 1)
		self.assertEqual(self.buyOrderList.volume, 100)
		self.assertEqual(self.sellOrderList.volume, 75)

class test_order_book(unittest.TestCase):

	def setUp(self):
		self.completed_trades = []
		self.completed_orders = []
		self.orders = []
		self.order_book = OrderBook("KEQ")
		for i in range(1, 10):
			quote = test_quotes[str(i)]
			if "price" in quote:
				quote["price"] = Decimal(quote["price"])
			order = json.loads(self.order_book.process_order(quote))
			self.orders.append(order)
			for trades in self.order_book.completed_trades:
				self.completed_trades.append(trades)
			for orders in self.order_book.completed_orders:
				self.completed_orders.append(orders)
		
	def test_get_min_ask(self):
		self.assertEqual(self.order_book.get_min_ask(), 99.5)

	def test_get_max_bid(self):
		self.assertEqual(self.order_book.get_max_bid(), 99)

	def test_process_order(self):
		self.assertEqual(len(self.order_book.bids.keys()), 1)
		self.assertEqual(len(self.order_book.asks.keys()), 2)
		self.assertEqual(len(self.completed_trades), 6)
		self.assertEqual(len(self.order_book.ongoing_orders), 3)
		self.assertEqual(len(self.completed_orders), 6)

	def test_modify_order(self):
		quote = test_quotes[str(10)]
		if "price" in quote:
			quote["price"] = Decimal(quote["price"])
		new_order = json.loads(self.order_book.modify_order(self.orders[8]["order_id"], quote))
		self.assertEqual(new_order["price"], '75')

	def test_cancel_order(self):
		quote = test_quotes[str(10)]
		if "price" in quote:
			quote["price"] = Decimal(quote["price"])
		new_order = json.loads(self.order_book.process_order(quote))
		self.order_book.cancel_order(new_order["order_id"])
		self.assertEqual(len(self.order_book.bids.keys()), 1)

class test_exchange(unittest.TestCase):

	def test_verify_endpoint(self):
		url = 'http://localhost:5000/v1/quote/verify'
		data = {
			"quote": test_quotes[str(1)]
		}
		headers = {'Content-type': 'application/json'}
		resp = requests.post(url, data=json.dumps(data), headers=headers)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.json()["valid"], True)

	def test_new_order_endpoint(self):
		url = 'http://localhost:5000/v1/order/new'
		data = {
			"quote": test_quotes[str(1)]
		}
		headers = {'Content-type': 'application/json'}
		resp = requests.post(url, data=json.dumps(data), headers=headers)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.json()["order"]["was_placed"], True)

	def test_order_book(self):
		url = 'http://localhost:5000/v1/order/book'
		resp = requests.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertTrue(resp.json()["bids"])

	def test_order_status(self):
		url1 = 'http://localhost:5000/v1/order/new'
		data1 = {
			"quote": test_quotes[str(1)]
		}
		headers1 = {'Content-type': 'application/json'}
		resp1 = requests.post(url1, data=json.dumps(data1), headers=headers1)
		print(resp1.json())
		url = 'http://localhost:5000/v1/order/status'
		data = {
			"order_id": resp1.json()["order"]["order_id"]
		}
		headers = {'Content-type': 'application/json'}
		resp = requests.post(url, data=json.dumps(data), headers=headers)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.json()["order"]["was_placed"], True)

if __name__=="__main__":
    unittest.main()