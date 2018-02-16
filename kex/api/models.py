import uuid

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models


class Account(models.Model):
    account_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. \
        Up to 15 digits allowed.",
    )
    phone_number = models.CharField(validators=[phone_regex], unique=True, max_length=15)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Trade(models.Model):
    trade_id = models.CharField(primary_key=True, max_length=500)
    buyer = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='buyer_account')
    seller = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='seller_account')
    created_at = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    symbol = models.CharField(max_length=10)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.quantity} {self.symbol} @ {self.price}: {self.buyer} & {self.seller}"

class Order(models.Model):
    order_id = models.CharField(primary_key=True, max_length=500)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    side = models.CharField(max_length=4)
    order_type = models.CharField(max_length=6)
    symbol = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(blank=True, null=True)
    trades = models.ManyToManyField(Trade, blank=True)

    def __str__(self):
        order_string = f"{self.side} - {self.quantity} {self.symbol} @ MARKET"
        if self.price:
            order_string = f"{self.side} - {self.quantity} {self.symbol} @ {self.price}"
        return order_string 
        
class Price(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    best_ask = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    best_bid = models.DecimalField(max_digits=10, decimal_places=2, blank=True)

    def __str__(self):
        return f"{self.created_at}: {self.best_bid} - {self.best_ask}"
