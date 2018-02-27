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
from rest_framework.decorators import detail_route
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


exchange_uri = 'http://localhost:5000'
new_endpoint = '/v1/order/new'
status_endpoint = '/v1/order/status'
edit_endpoint = '/v1/order/edit'
cancel_endpoint = '/v1/order/cancel'
verify_endpoint = '/v1/quote/verify'

class CreateListUpdateRetrieveViewSet(mixins.CreateModelMixin,
                                mixins.ListModelMixin,
                                mixins.UpdateModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    pass

class UserViewSet(CreateListUpdateRetrieveViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)

class AccountViewSet(CreateListUpdateRetrieveViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = (permissions.IsAdminUser,)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('account',)
    permission_classes = (permissions.IsAuthenticated,)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def create(self, request):
        account = Account.objects.get(user=request.user)
        serializer=self.get_serializer(data=request.data)
        if serializer.is_valid():
            if account == request.data["account"] or request.user.is_staff:
                order_data = serializer.validated_data
                quote = {
                    "quote": 
                        {
                            "account_id": str(account.account_id),
                            "side": order_data["side"],
                            "type": order_data["order_type"],
                            "symbol": order_data["symbol"],
                            "quantity": order_data["quantity"],
                            "price": str(order_data["price"]),
                        }
                }
                try:
                    check_quote = requests.post(url=f"{exchange_uri}{verify_endpoint}", 
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(quote))
                except Exception as e:
                    return Response({"errors": [{"API_ERROR": e}],
                        "status_code": status.HTTP_503_SERVICE_UNAVAILABLE})
                valid_quote = check_quote.json()["valid"]
                if valid_quote:
                    try:
                        place_order = requests.post(url=f"{exchange_uri}{new_endpoint}",
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(quote))
                        order = place_order.json()
                        serializer.save(order_id = order["order"]["order_id"], 
                            was_placed = order["order"]["was_placed"],
                            was_filled = order["order"]["was_filled"],
                            was_cancelled = order["order"]["was_cancelled"])
                    except Exception as e:
                        return Response({"errors": [{"API_ERROR": e}],
                        "status_code": status.HTTP_503_SERVICE_UNAVAILABLE})
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response({"errors": [{"ORDER_ERROR": "Invalid quote."}],
                        "status_code": status.HTTP_400_BAD_REQUEST})
            else:
                return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                    "status_code": status.HTTP_401_UNAUTHORIZED})
        else:
            return Response({"errors": serializer.errors,
                "status_code": status.HTTP_400_BAD_REQUEST})
            
    def retrieve(self, request, pk):
        account = Account.objects.get(user=request.user)
        order = Order.objects.get(pk=pk)
        if account == order.account or request.user.is_staff:
            serializer=OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"errors": [{"ORDER_ERROR": "Incorrect account ID or API Key."}],
                "status_code": status.HTTP_401_UNAUTHORIZED})

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def edit(self, request, pk):
        pass

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk):
        pass

class TradeViewSet(CreateListUpdateRetrieveViewSet):
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    permission_classes = (permissions.IsAdminUser,)

class PriceViewSet(CreateListUpdateRetrieveViewSet):
    queryset = Price.objects.all()
    serializer_class = PriceSerializer
    permission_classes = (permissions.IsAdminUser,)
