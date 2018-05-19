import json

from django.conf import settings
from django.core import serializers
from django.contrib.auth.models import User
from django_filters import rest_framework as filters
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from rest_framework import mixins
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.views import APIView
import requests

from kex.api.models import Account
from kex.api.models import Order
from kex.api.models import Trade
from kex.api.models import Price
from kex.api.permissions import IsOwnerOrReadOnly
from kex.api.serializers import AccountSerializer
from kex.api.serializers import OrderSerializer
from kex.api.serializers import TradeSerializer
from kex.api.serializers import PriceSerializer
from kex.api.serializers import UserSerializer


SYMBOL = "KEQ"
exchange_uri = 'http://localhost:5000'
new_endpoint = '/v1/order/new'
status_endpoint = '/v1/order/status'
edit_endpoint = '/v1/order/edit'
cancel_endpoint = '/v1/order/cancel'
verify_endpoint = '/v1/quote/verify'
price_endpoint = '/v1/price/best'
trade_details_endpoint = '/v1/trade/details'

class AccountCreateView(viewsets.GenericViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request):
        serializer = UserSerializer(data = request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                token = Token.objects.get_or_create(user = user)
                account_data = {
                    "user": user.id,
                    "phone_number": request.data['phone_number'],
                    "token": token[0].key
                }
                account_serializer = AccountSerializer(data = account_data)
                if account_serializer.is_valid():
                    account_serializer.save()
                    return Response(account_serializer.data, status=status.HTTP_201_CREATED)
                else:
                    user.delete()
                    token[0].delete()
                    return Response(account_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AccountViewSet(viewsets.GenericViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def retrieve(self, request, pk):
        try:
            account = Account.objects.get(pk=pk)
        except:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})
        if account.token == Token.objects.get(user = request.user):
            return Response(AccountSerializer(account).data, status=status.HTTP_200_OK)
        else:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})

    def partial_update(self, request, pk):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        try:
            account = Account.objects.get(pk=pk)
        except:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})
        if account.token == Token.objects.get(user = request.user):
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.filter(was_filled = False)
    serializer_class = OrderSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('account',)
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request):
        try:
            account = Account.objects.get(user=request.user)
        except:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})
        if account == request.data["account"] or request.user.is_staff:
            order_data = request.data
            quote = {
                "quote":
                    {
                        "account_id": str(account.account_id),
                        "side": order_data["side"],
                        "order_type": order_data["order_type"],
                        "symbol": SYMBOL,
                        "quantity": int(order_data["quantity"]),
                        "price": str(order_data["price"]),
                    }
            }
            try:
                check_quote = requests.post(url=f"{exchange_uri}{verify_endpoint}",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(quote))
            except Exception as e:
                return Response({"errors": [{"API_ERROR": str(e)}],
                    "status_code": status.HTTP_503_SERVICE_UNAVAILABLE})
            valid_quote = check_quote.json()["valid"]
            if valid_quote:
                try:
                    place_order = requests.post(url=f"{exchange_uri}{new_endpoint}",
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(quote))
                    order = place_order.json()
                    if "order" in order:
                        serializer = self._update_order_trades_price(order)
                    else:
                        return Response({"errors": order["errors"],
                            "status_code": status.HTTP_400_BAD_REQUEST})
                except Exception as e:
                    return Response({"errors": [{"API_ERROR": str(e)}],
                    "status_code": status.HTTP_503_SERVICE_UNAVAILABLE})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({"errors": [{"ORDER_ERROR": "Invalid quote."}],
                    "status_code": status.HTTP_400_BAD_REQUEST})
        else:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})

    def retrieve(self, request, pk):
        try:
            account = Account.objects.get(user=request.user)
        except:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})
        try:
            order = Order.objects.get(pk=pk)
        except:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect order ID."}],
                "status_code": status.HTTP_400_BAD_REQUEST})
        if account == order.account or request.user.is_staff:
            serializer=OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def edit(self, request, pk):
        try:
            account = Account.objects.get(user=request.user)
        except:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})
        try:
            order = Order.objects.get(pk=pk)
        except:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect order ID."}],
                "status_code": status.HTTP_400_BAD_REQUEST})
        updated_data = request.data
        if account == order.account or request.user.is_staff:
            quote = {
                "quote": {
                    "account_id": str(account.account_id),
                    "side": order.side,
                    "order_type": order.order_type,
                    "symbol": order.symbol,
                    "quantity": order.quantity,
                    "price": str(order.price),
                },
                "order_id": str(order.order_id)
            }
            if "side" in updated_data:
                quote["quote"]["side"] = updated_data["side"]
            if "order_type" in updated_data:
                quote["quote"]["order_type"] = updated_data["order_type"]
            if "quantity" in updated_data:
                quote["quote"]["quantity"] = int(updated_data["quantity"])
            if "price" in updated_data:
                quote["quote"]["price"] = updated_data["price"]
            try:
                check_quote = requests.post(url=f"{exchange_uri}{verify_endpoint}",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(quote))
            except Exception as e:
                return Response({"errors": [{"API_ERROR": str(e)}],
                    "status_code": status.HTTP_503_SERVICE_UNAVAILABLE})
            valid_quote = check_quote.json()["valid"]
            if valid_quote:
                try:
                    edit_order = requests.post(url=f"{exchange_uri}{edit_endpoint}",
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(quote))
                    new_order = edit_order.json()
                    if "order" in new_order:
                        serializer = self._update_order_trades_price(new_order)
                        order.delete()
                    else:
                        return Response({"errors": new_order["errors"],
                            "status_code": status.HTTP_400_BAD_REQUEST})
                except Exception as e:
                    return Response({"errors": [{"API_ERROR": str(e)}],
                    "status_code": status.HTTP_503_SERVICE_UNAVAILABLE})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({"errors": [{"ORDER_ERROR": "Invalid quote."}],
                    "status_code": status.HTTP_400_BAD_REQUEST})
        else:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk):
        try:
            account = Account.objects.get(user=request.user)
        except:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})
        try:
            order = Order.objects.get(pk=pk)
        except:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect order ID."}],
                "status_code": status.HTTP_400_BAD_REQUEST})
        if account == order.account or request.user.is_staff:
            try:
                cancel_order = requests.post(url=f"{exchange_uri}{cancel_endpoint}",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps({"order_id": order.order_id}))
            except Exception as e:
                return Response({"errors": [{"API_ERROR": str(e)}],
                    "status_code": status.HTTP_503_SERVICE_UNAVAILABLE})
            if "order_id" in cancel_order.json():
                if cancel_order.json()["was_cancelled"]:
                    order.delete()
            else:
                return Response({"errors": cancel_order.json()["errors"],
                    "status_code": status.HTTP_400_BAD_REQUEST})
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        else:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})

    def _update_order_trades_price(self, new_order):
        new_order["order"]["account"] = new_order["order"]["account_id"]
        trades = new_order["order"]["trades"]
        new_order["order"]["trades"] = []
        serializer = self.get_serializer(data = new_order["order"])
        serializer.is_valid(raise_exception = True)
        serializer.save()
        for trade in trades:
            try:
                trade_object = Trade.objects.get(trade_id = trade)
            except:
                try:
                    trade_details = requests.post(url=f"{exchange_uri}{trade_details_endpoint}",
                        headers={"Content-Type": "application/json"},
                        data=json.dumps({"trade_id": trade}))
                except Exception as e:
                    return Response({"errors": [{"API_ERROR": str(e)}],
                        "status_code": status.HTTP_503_SERVICE_UNAVAILABLE})
                if "trade" in trade_details.json():
                    new_trade = trade_details.json()["trade"]
                    new_trade["created_at"] = new_trade["timestamp"]
                    new_trade["buyer"] = new_trade["buyer"][0]
                    new_trade["seller"] = new_trade["seller"][0]
                    update_orders = [new_trade["buying_order"], new_trade["selling_order"]]
                    trade_serializer = TradeSerializer(data = new_trade)
                    trade_serializer.is_valid(raise_exception = True)
                    trade_serializer.save()
                    for orders in update_orders:
                        try:
                            order_details = requests.post(url=f"{exchange_uri}{status_endpoint}",
                                headers={"Content-Type": "application/json"},
                                data=json.dumps({"order_id": orders}))
                        except Exception as e:
                            return Response({"errors": [{"API_ERROR": str(e)}],
                                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE})
                        if "order" in order_details.json():
                            updated_order = Order.objects.get(order_id = orders)
                            updated_order.quantity = order_details.json()["order"]["quantity"]
                            updated_order.was_filled = order_details.json()["order"]["was_filled"]
                            updated_order.save()
                        else:
                            return Response({"errors": order_details["errors"],
                                "status_code": status.HTTP_400_BAD_REQUEST})
                else:
                    return Response({"errors": trade["errors"],
                        "status_code": status.HTTP_400_BAD_REQUEST})
        serializer.save(trades = trades)
        try:
            price_details = requests.get(url=f"{exchange_uri}{price_endpoint}")
        except Exception as e:
            return Response({"errors": [{"API_ERROR": str(e)}],
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE})
        price_serializer = PriceSerializer(data = price_details.json())
        price_serializer.is_valid(raise_exception = True)
        price_serializer.save()
        return serializer

class TradeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    permission_classes = (permissions.IsAuthenticated,)

class PriceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Price.objects.all()
    serializer_class = PriceSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @list_route(methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def now(self, request):
        try:
            most_recent_price = Price.objects.last()
        except:
            return Response({"errors": [{"PRICE_ERROR": "No historical prices."}],
                "status_code": status.HTTP_400_BAD_REQUEST})
        return Response(PriceSerializer(most_recent_price).data, status=status.HTTP_200_OK)
