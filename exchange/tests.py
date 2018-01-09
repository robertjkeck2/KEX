import json
import unittest

from orderbook import Order, OrderList, OrderBook


with open("test_quotes.json") as f:
	test_quotes = json.load(f)

class test_orders(unittest.TestCase):

	def setUp(self):
		self.order = Order(test_quotes[str(1)])
		self.order2 = Order(test_quotes[str(7)])

	def test_add_order(self):
		self.assertEqual(self.order.price, 100.00)
		self.assertEqual(self.order.side, "BUY")
		self.assertEqual(self.order.quantity, 50)
		self.assertEqual(self.order.account_id, "1")
		self.assertEqual(self.order2.price, None)
		self.assertEqual(self.order2.side, "BUY")
		self.assertEqual(self.order2.quantity, 100)
		self.assertEqual(self.order2.account_id, "7")

	def test_update_order(self):
		self.order.update(75)
		self.assertEqual(self.order.quantity, 75)

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
			order = self.order_book.process_order(test_quotes[str(i)])
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
		self.assertEqual(len(self.completed_orders), 6)

	def test_modify_order(self):
		new_order = self.order_book.modify_order(self.orders[8], test_quotes[str(10)])
		self.assertEqual(new_order.price, 100)

	def test_cancel_order(self):
		self.order_book.cancel_order(self.orders[8])
		self.assertEqual(len(self.order_book.bids.keys()), 0)

if __name__=="__main__":
    unittest.main()