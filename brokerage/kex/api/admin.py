from django.contrib import admin
from rest_framework.authtoken.admin import TokenAdmin

from kex.api.models import Account
from kex.api.models import Order
from kex.api.models import Trade
from kex.api.models import Price


admin.site.register(Account)
admin.site.register(Order)
admin.site.register(Trade)
admin.site.register(Price)
TokenAdmin