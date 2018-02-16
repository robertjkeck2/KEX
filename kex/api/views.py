from rest_framework import mixins
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.core import serializers
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

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


class CreateListRetrieveViewSet(mixins.CreateModelMixin,
                                mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    pass

class UsersViewSet(CreateListRetrieveViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

class OrderViewSet(CreateListRetrieveViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

class TradeViewSet(CreateListRetrieveViewSet):
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

class PriceViewSet(CreateListRetrieveViewSet):
    queryset = Price.objects.all()
    serializer_class = PriceSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

class LoginView(APIView):
    def post(self, request, format=None):
        if User.objects.filter(username=request.data["username"]).exists():
            user = User.objects.get(username=request.data["username"])
            if user.check_password(request.data["password"]):
                return JsonResponse({"logged_in": True, "message": "Successfully logged in!"})
        return JsonResponse({"logged_in": False, "message": "Username/password combo does not exist"})