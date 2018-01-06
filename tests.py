import unittest

from orderbook import Order, OrderList, OrderBook


test_quote1 = {
	"account_id": "1",
	"side": "BUY",
	"type": "LIMIT",
	"symbol": "KEQ",
	"price": 100.00,
	"quantity": 50,
}
test_quote2 = {
	"account_id": "2",
	"side": "SELL",
	"type": "LIMIT",
	"symbol": "KEQ",
	"price": 100.50,
	"quantity": 50,
}
test_quote3 = {
	"account_id": "3",
	"side": "BUY",
	"type": "LIMIT",
	"symbol": "KEQ",
	"price": 100.00,
	"quantity": 100,
}
test_quote4 = {
	"account_id": "4",
	"side": "SELL",
	"type": "LIMIT",
	"symbol": "KEQ",
	"price": 100.50,
	"quantity": 75,
}
test_quote5 = {
	"account_id": "5",
	"side": "BUY",
	"type": "LIMIT",
	"symbol": "KEQ",
	"price": 101.00,
	"quantity": 150,
}
test_quote6 = {
	"account_id": "6",
	"side": "SELL",
	"type": "LIMIT",
	"symbol": "KEQ",
	"price": 99.50,
	"quantity": 300,
}
test_quote7 = {
	"account_id": "7",
	"side": "BUY",
	"type": "MARKET",
	"symbol": "KEQ",
	"quantity": 100,
}
test_quote8 = {
	"account_id": "8",
	"side": "BUY",
	"type": "MARKET",
	"symbol": "KEQ",
	"quantity": 5,
}
test_quote9 = {
	"account_id": "9",
	"side": "SELL",
	"type": "LIMIT",
	"symbol": "KEQ",
	"price": 101.00,
	"quantity": 150,
}
test_quote10 = {
	"account_id": "10",
	"side": "SELL",
	"type": "LIMIT",
	"symbol": "KEQ",
	"price": 99.50,
	"quantity": 300,
}
test_quote11 = {
	"account_id": "11",
	"side": "BUY",
	"type": "MARKET",
	"symbol": "KEQ",
	"quantity": 100,
}
test_quote12 = {
	"account_id": "12",
	"side": "BUY",
	"type": "MARKET",
	"symbol": "KEQ",
	"quantity": 200,
}
test_quote13 = {
	"account_id": "13",
	"side": "BUY",
	"type": "LIMIT",
	"symbol": "KEQ",
	"price": 99.00,
	"quantity": 100,
}
test_quote14 = {
	"account_id": "10",
	"side": "BUY",
	"type": "LIMIT",
	"symbol": "KEQ",
	"price": 100.00,
	"quantity": 100,
}

class test_orders(unittest.TestCase):

	def setUp(self):
		self.order = Order(test_quote1)
		self.order2 = Order(test_quote7)

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
		test_quotes = [test_quote1, test_quote2, test_quote3, test_quote4]
		for i in range(0, len(test_quotes)):
			self.orders.append(Order(test_quotes[i]))
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
		test_quotes = [test_quote1, test_quote2, test_quote3, test_quote4, test_quote5, test_quote6, test_quote7, test_quote8]
		self.order_book = OrderBook("KEQ")
		for keys in self.order_book.order_store.keys(): self.order_book.order_store.delete(keys)
		for i in range(0, len(test_quotes)):
			order = self.order_book.process_order(test_quotes[i])
			print(self.order_book)
		new_order = self.order_book.modify_order(order, test_quote14)
		self.order_book.cancel_order(new_order)
		
	def test_process_order(self):
		print(self.order_book)
		print(sorted(self.order_book.order_store.keys()))

if __name__=="__main__":
    unittest.main()