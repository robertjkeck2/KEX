from datetime import datetime
from decimal import Decimal
import json
from os import path
import pickle

from bson.binary import Binary
from flask import Flask, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from redis import StrictRedis, RedisError

from orderbook import OrderBook
from orderbook import OrderError, PriceError, MarketError


STOCK_SYMBOL = "KEQ"
ORDERBOOK_FILE = 'orderbook.pickle'

app = Flask(__name__)
redis = StrictRedis(host="localhost", port=6379, db=0, charset="utf-8", decode_responses=True)
mongo = MongoClient(host="localhost")
db = mongo.exchange_db

@app.route("/v1/quote/verify", methods=["POST"])
def check():
    quote = request.get_json()["quote"]
    if "price" in quote:
        quote["price"] = Decimal(quote["price"])
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
    if "price" in quote:
        quote["price"] = Decimal(quote["price"])
    valid, errors = _check_quote(quote)
    response = {}
    if valid:
        try:
            order = json.loads(orderbook.process_order(quote))
            _backup_orderbook(orderbook)
            order["was_placed"] = True
            order["was_filled"] = False
            try:
                redis.set(order["order_id"], json.dumps(order))
                _update_redis()
            except RedisError as err:
                errors.append({"REDIS_ERROR": str(err)})
                pass
            if order["order_id"] not in str(redis.keys()):
                order["was_filled"] = True
            response["order"] = order
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
    errors = []
    try:
        if order_id not in str(redis.keys()):
            order_store = db.orders.find({'order_id': order_id}, {"_id": 0}).limit(1)
            if order_store.count() > 0:
                order = order_store[0]
                order["was_placed"] = True
                order["was_filled"] = True
            else:
                order = {}
                response["errors"] = [{"ORDER_ERROR": "No order with that order ID currently exists."}]
        else:
            order = json.loads(redis.get(order_id))
            order["was_placed"] = True
            order["was_filled"] = False
        response["order"] = order
    except RedisError as err:
        errors.append({"REDIS_ERROR": str(err)})
        pass
    if errors:
        response["errors"] = errors
    return json.dumps(response)

@app.route("/v1/order/edit", methods=["POST"])
def modify():
    quote = request.get_json()["quote"]
    if "price" in quote:
        quote["price"] = Decimal(quote["price"])
    order_id = request.get_json()["order_id"]
    valid, errors = _check_quote(quote)
    response = {}
    if valid:
        try:
            new_order = json.loads(orderbook.modify_order(order_id, quote))
            _backup_orderbook(orderbook)
            new_order["was_placed"] = True
            new_order["was_filled"] = False
            try:
                redis.delete(order_id)
                redis.set(new_order["order_id"], json.dumps(new_order))
                _update_redis()
            except RedisError as err:
                errors.append({"REDIS_ERROR": str(err)})
                pass
            if new_order["order_id"] not in str(redis.keys()):
                new_order["was_filled"] = True
            response["order"] = new_order
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
        _backup_orderbook(orderbook)
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
    best_ask = orderbook.get_min_ask()
    best_bid = orderbook.get_max_bid()
    response["best_ask"] = best_ask
    response["best_bid"] = best_bid
    if not best_ask:
        response["best_ask"] = "N/A"
    if not best_bid:
        response["best_bid"] = "N/A"
    current_time = str(datetime.now())
    response["time"] = current_time
    return json.dumps(response)

@app.route("/v1/order/book", methods=["GET"])
def order_book():
    response = {}
    bids = {}
    asks = {}
    bid_volume = [bids.update({str(key): orderbook.bids[key].volume}) for key in orderbook.bids.keys()]
    ask_volume = [asks.update({str(key): orderbook.asks[key].volume}) for key in orderbook.asks.keys()]
    response["bids"] = bids
    response["asks"] = asks
    current_time = str(datetime.now())
    response["timestamp"] = current_time
    return json.dumps(response)

@app.route("/v1/trade/details", methods=["POST"])
def trade_details():
    trade_id = request.get_json()["trade_id"]
    response = {}
    errors = []
    try:
        trade = db.trades.find_one({"trade_id": trade_id})
        if trade:
            trade.pop("_id", None)
            response["trade"] = trade
        else:
            errors.append({"TRADE_ERROR": "No trade with that trade ID currently exists."})
    except PyMongoError as err:
        errors.append({"MONGODB_ERROR": str(err)})
        pass
    if errors:
        response["errors"] = errors
    return json.dumps(response)


def _check_quote(quote):
    valid = False
    errors = []
    if quote["side"] != "BUY" and quote["side"] != "SELL":
        errors.append({"SIDE_ERROR": "Incorrect BUY/SELL side format."})
    if quote["order_type"] != "MARKET" and quote["order_type"] != "LIMIT":
        errors.append({"TYPE_ERROR": "Incorrect LIMIT/MARKET side format."})
    if quote["symbol"] != STOCK_SYMBOL:
        errors.append({"SYMBOL_ERROR": "Incorrect stock symbol for this exchange."})
    if quote["order_type"] == "LIMIT" and float(quote["price"]) <= 0:
        errors.append({"PRICE_ERROR": "Price must be greater than 0."})
    if int(quote["quantity"]) <= 0:
        errors.append({"QUANTITY_ERROR": "Quantity must be greater than 0."})
    if not errors:
        valid = True
    return valid, errors

def _setup_orderbook():
    [redis.delete(key) for key in redis.keys()]
    orderbook_store = db.orderbook.find({'orderbook_id': 1}).limit(1)
    if path.isfile(ORDERBOOK_FILE):
        with open(ORDERBOOK_FILE, 'rb') as f:
            orderbook = pickle.load(f)
    elif orderbook_store.count() > 0:
        orderbook = pickle.loads(orderbook_store[0]["orderbook"])
    else:
        orderbook = OrderBook(STOCK_SYMBOL)
    return orderbook

def _update_redis():
    for ids, orders in orderbook.ongoing_orders.items():
        redis.set(ids, orders)
    if hasattr(orderbook, 'completed_orders'):
        for ids, orders in orderbook.completed_orders.items():
            db.orders.insert_one(json.loads(orders))
            redis.delete(ids)
    if hasattr(orderbook, 'completed_trades'):
        for trades in orderbook.completed_trades.values():
            db.trades.insert_one(json.loads(trades))

def _backup_orderbook(orderbook):
    with open(ORDERBOOK_FILE, 'wb') as f:
        pickle.dump(orderbook, f)
    orderbook_string = pickle.dumps(orderbook)
    db.orderbook.replace_one({'orderbook_id': 1}, {'orderbook_id': 1, 'orderbook': Binary(orderbook_string)}, upsert=True)

if __name__ == "__main__":
    orderbook = _setup_orderbook()
    _update_redis()
    app.run(host='0.0.0.0', port=5000, debug=True)
