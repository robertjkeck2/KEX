from datetime import datetime
import json
from flask import Flask
from redis import Redis, RedisError

from orderbook import OrderBook


STOCK_SYMBOL = "KEQ"

app = Flask(__name__)
redis = Redis(host="localhost", port=6379, db=0)

orderbook = OrderBook(STOCK_SYMBOL)

@app.route("/process_trade", methods=["POST"])
def process(quote):
	order = orderbook.process_order(order)


@app.route("/modify_trade", methods=["POST"])
def modify(order_id, quote):
	return "yo"


@app.route("/cancel_trade", methods=["POST"])
def cancel(order_id):
	return "yo"

@app.route("/get_current_price", methods=["GET"])
def price():
	current_price = orderbook.get_min_ask()
	current_time = str(datetime.now())
	response = {
		"time": current_time,
		"current_price": current_price
	}
	if not current_price:
		response["errors"] = {
			"PRICE_ERROR": "No current sellers in the market."
		}
		response["current_price"] = None
	return json.dumps(response)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)