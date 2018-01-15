from datetime import datetime
import json
from flask import Flask, request
from redis import Redis, RedisError

from orderbook import OrderBook
from orderbook import OrderError, PriceError, MarketError


STOCK_SYMBOL = "KEQ"

app = Flask(__name__)
redis = Redis(host="localhost", port=6379, db=0)

orderbook = OrderBook(STOCK_SYMBOL)

@app.route("/check_quote", methods=["POST"])
def check():
    quote = request.get_json()
    current_time = str(datetime.now())
    valid, errors = _check_quote(quote)
    response = {
        "time": current_time,
        "valid": valid,
    }
    if not valid:
        response["errors"] = errors
    return json.dumps(response)

@app.route("/process_trade", methods=["POST"])
def process():
    quote = request.get_json()
    current_time = str(datetime.now())
    valid, errors = _check_quote(quote)
    response = {
        "time": current_time,
    }
    if valid:
        try:
            order = json.loads(orderbook.process_order(quote))
            response["order_id"] = order["order_id"]
            response["filled"] = True
            response["quote"] = quote
            try:
                redis.set(order["order_id"], json.dumps(order))
                for ids, orders in orderbook.ongoing_orders.items():
                    redis.set(ids, orders)
                for orders in orderbook.completed_orders.keys():
                    redis.delete(orders)
            except RedisError as err:
                errors.append(err)
                pass
            if order["order_id"] in redis.keys():
                response["filled"] = False
        except OrderError as err:
            errors.append({"ORDER_ERROR": err.message})
            pass
        except MarketError as err:
            errors.append({"MARKET_ERROR": err.message})
            pass
        except PriceError as err:
            errors.append({"PRICE_ERROR": err.message})
            pass
    if errors:
        response["errors"] = errors
    return json.dumps(response)

@app.route("/modify_trade/<order_id>", methods=["POST"])
def modify(order_id):
    order = redis.get(order_id)
    print(json.loads(order))
    quote = request.get_json()
    current_time = str(datetime.now())
    valid, errors = _check_quote(quote)
    response = {
        "time": current_time,
    }
    if valid:
        try:
            new_order = json.loads(orderbook.modify_order(order, quote))
            response["order_id"] = order["order_id"]
            response["filled"] = True
            response["quote"] = quote
            try:
                redis.delete(order["order_id"])
                redis.set(new_order["order_id"], json.dumps(new_order))
                for ids, orders in orderbook.ongoing_orders.items():
                    redis.set(ids, orders)
                for orders in orderbook.completed_orders.keys():
                    redis.delete(orders)
            except RedisError as err:
                errors.append(err)
                pass
            if new_order["order_id"] in redis.keys():
                response["filled"] = False
        except OrderError as err:
            errors.append({"ORDER_ERROR": err.message})
            pass
        except MarketError as err:
            errors.append({"MARKET_ERROR": err.message})
            pass
        except PriceError as err:
            errors.append({"PRICE_ERROR": err.message})
            pass
        if errors:
            response["errors"] = errors
        return json.dumps(response)

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

def _check_quote(quote):
    valid = False
    errors = []
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
    if not errors:
        valid = True
    return valid, errors

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)