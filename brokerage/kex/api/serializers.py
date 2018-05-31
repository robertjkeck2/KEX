from rest_framework import serializers
from django.contrib.auth.models import User

from kex.api.models import Account
from kex.api.models import Order
from kex.api.models import Trade
from kex.api.models import Price


class AccountSerializer(serializers.ModelSerializer):

	class Meta:
		model = Account
		fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):

	class Meta:
		model = Order
		fields = '__all__'

class TradeSerializer(serializers.ModelSerializer):

	class Meta:
		model = Trade
		fields = '__all__'
		
class PriceSerializer(serializers.ModelSerializer):

	class Meta:
		model = Price
		fields = '__all__'

class UserSerializer(serializers.ModelSerializer):

	class Meta:
		model = User
		fields = ('id','username','first_name','last_name','email',)
		write_only_fields = ('password',)
		read_only_fields = ('id','is_active','is_staff',)

	def create(self, validated_data):
		user = User.objects.create_user(**validated_data)
		return user

