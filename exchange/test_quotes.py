import random


def create_random_quote(symbol, price_floor, price_ceiling):
	side_mapping = {0: "BUY", 1: "SELL"}
	type_mapping = {0: "LIMIT", 1: "MARKET"}
	order_type = type_mapping[random.randint(0,1)]
	price = None
	if order_type == "LIMIT":
		price = round(random.randint(price_floor, price_ceiling - 1) + random.random(), 2)
	random_quote = {
		"account_id": random.randint(1,100000),
		"side": side_mapping[random.randint(0,1)],
		"order_type": order_type,
		"symbol": symbol,
		"price": price,
		"quantity": random.randint(1,100)
	}
	return random_quote

print(create_random_quote("KEQ", 50, 55))
