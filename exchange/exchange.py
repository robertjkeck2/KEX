from datetime import datetime
import json
from flask import Flask
from redis import Redis, RedisError

from orderbook import OrderBook


STOCK_SYMBOL = "KEQ"

app = Flask(__name__)
redis = Redis(host="localhost", port=6379, db=0)

orderbook = OrderBook(STOCK_SYMBOL)

@app.route("/check_quote", methods=["POST"])
def check(quote):
    errors = []
    current_time = str(datetime.now())
    if quote["side"] != "BUY" and quote["side"] != "SELL":
        errors.append({"SIDE_ERROR": "Incorrect BUY/SELL side format."})
    if quote["type"] != "MARKET" and quote["type"] != "LIMIT":
        errors.append({"TYPE_ERROR": "Incorrect LIMIT/MARKET side format."})
    if quote["symbol"] != STOCK_SYMBOL:
        errors.append({"SYMBOL_ERROR": "Incorrect stock symbol for this exchange."})
    if quote["price"] <= 0:
        errors.append({"PRICE_ERROR": "Price must be greater than 0."})
    if quote["quantity"] <= 0:
        errors.append({"QUANTITY_ERROR": "Quantity must be greater than 0."})
    response = {
        "time": current_time,
        "errors": errors
    }
    return response

@app.route("/process_trade", methods=["POST"])
def process(quote):
    order = orderbook.process_order(quote)

@app.route("/modify_trade", methods=["POST"])
def modify(order_id, quote):
    order = redis.get(order_id)
    try:
        new_order = orderbook.modify_order(order, quote)
    except Exception as err:
        pass

@app.route("/cancel_trade", methods=["POST"])
def cancel(order_id):
    order = redis.get(order_id)
    try:
        orderbook.cancel_order(order)
    except Exception as err:
        pass

@app.route("/get_current_price", methods=["GET"])
def price():
    current_price = orderbook.get_min_ask()
    current_time = str(datetime.now())
    response = {
        "time": current_time
    }
    if not current_price:
        response["errors"] = [{"PRICE_ERROR": "No current sellers in the market."}]
    else:
        response["current_price"] = current_price
    return json.dumps(response)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)