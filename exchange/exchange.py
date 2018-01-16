from datetime import datetime
import json
from flask import Flask, request
from redis import StrictRedis, RedisError

from orderbook import OrderBook
from orderbook import OrderError, PriceError, MarketError


STOCK_SYMBOL = "KEQ"

app = Flask(__name__)
redis = StrictRedis(host="localhost", port=6379, db=0, charset="utf-8", decode_responses=True)
[redis.delete(key) for key in redis.keys()]

orderbook = OrderBook(STOCK_SYMBOL)

@app.route("/v1/quote/verify", methods=["POST"])
def check():
    quote = request.get_json()["quote"]
    valid, errors = _check_quote(quote)
    response = {}
    response["valid"] = valid
    if not valid:
        response["errors"] = errors
    current_time = str(datetime.now())
    response["timestamp"] = current_time
    return json.dumps(response)

@app.route("/v1/order/new", methods=["POST"])
def process():
    quote = request.get_json()["quote"]
    valid, errors = _check_quote(quote)
    response = {}
    if valid:
        try:
            order = json.loads(orderbook.process_order(quote))
            response["order"] = order
            response["was_placed"] = True
            response["was_filled"] = False
            response["quote"] = quote
            try:
                redis.set(order["order_id"], json.dumps(order))
                _update_redis()
            except RedisError as err:
                errors.append({"REDIS_ERROR": str(err)})
                pass
            if order["order_id"] not in str(redis.keys()):
                response["was_filled"] = True
        except OrderError as err:
            errors.append({"ORDER_ERROR": str(err)})
            pass
        except MarketError as err:
            errors.append({"MARKET_ERROR": str(err)})
            pass
        except PriceError as err:
            errors.append({"PRICE_ERROR": str(err)})
            pass
    if errors:
        response["errors"] = errors
    return json.dumps(response)

@app.route("/v1/order/status", methods=["POST"])
def status():
    order_id = request.get_json()["order_id"]
    response = {}
    if order_id not in str(redis.keys()):
        response["was_filled"] = True
    else:
        order = json.loads(redis.get(order_id))
        response["order"] = order
        response["was_filled"] = False
    return json.dumps(response)

@app.route("/v1/order/edit", methods=["POST"])
def modify():
    quote = request.get_json()["quote"]
    order_id = request.get_json()["order_id"]
    valid, errors = _check_quote(quote)
    response = {}
    if valid:
        try:
            new_order = json.loads(orderbook.modify_order(order_id, quote))
            response["order"] = new_order
            response["was_placed"] = True
            response["was_filled"] = False
            response["quote"] = quote
            try:
                redis.delete(order_id)
                redis.set(new_order["order_id"], json.dumps(new_order))
                _update_redis()
            except RedisError as err:
                errors.append({"REDIS_ERROR": str(err)})
                pass
            if new_order["order_id"] not in str(redis.keys()):
                response["filled"] = True
        except OrderError as err:
            errors.append({"ORDER_ERROR": str(err)})
            pass
        except MarketError as err:
            errors.append({"MARKET_ERROR": str(err)})
            pass
        except PriceError as err:
            errors.append({"PRICE_ERROR": str(err)})
            pass
        if errors:
            response["errors"] = errors    
    return json.dumps(response)

@app.route("/v1/order/cancel", methods=["POST"])
def cancel():
    order_id = request.get_json()["order_id"]
    errors = []  
    response = {}
    try:
        orderbook.cancel_order(order_id)
        response["order_id"] = order_id
        response["was_cancelled"] = False
        current_time = str(datetime.now())
        response["timestamp"] = current_time
        try:
            redis.delete(order_id)
            _update_redis()
        except RedisError as err:
            errors.append({"REDIS_ERROR": str(err)})
            pass
        if order_id not in str(redis.keys()):
            response["was_cancelled"] = True
    except OrderError as err:
        errors.append({"ORDER_ERROR": str(err)})
        pass
    if errors:
        response["errors"] = errors
    return json.dumps(response)

@app.route("/v1/price/best", methods=["GET"])
def price():
    response = {}
    current_price = orderbook.get_min_ask()
    if not current_price:
        response["errors"] = [{"PRICE_ERROR": "No current sellers in the market."}]
    else:
        response["current_price"] = current_price
        current_time = str(datetime.now())
        response["time"] = current_time
    return json.dumps(response)

@app.route("/v1/order/book", methods=["GET"])
def order_book():
    response = {}
    bids = {}
    asks = {}
    bid_volume = [bids.update({key: orderbook.bids[key].volume}) for key in orderbook.bids.keys()]
    ask_volume = [asks.update({key: orderbook.asks[key].volume}) for key in orderbook.asks.keys()]
    response["bids"] = bids
    response["asks"] = asks
    current_time = str(datetime.now())
    response["timestamp"] = current_time
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

def _update_redis():
    for ids, orders in orderbook.ongoing_orders.items():
        redis.set(ids, orders)
    for orders in orderbook.completed_orders.keys():
        redis.delete(orders)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)