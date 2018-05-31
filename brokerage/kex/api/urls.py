from django.urls import include, path
from rest_framework.authtoken import views as auth_views
from rest_framework.routers import DefaultRouter
from kex.api import views


router = DefaultRouter()
router.register(r'register', views.AccountCreateView)
router.register(r'account', views.AccountViewSet)
router.register(r'order', views.OrderViewSet)
router.register(r'trade', views.TradeViewSet)
router.register(r'price', views.PriceViewSet)

urlpatterns = [
	path('', include(router.urls)),
	path('obtain_token/', auth_views.obtain_auth_token, name='auth'),
	path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
