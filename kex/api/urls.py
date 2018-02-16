from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from kex.api import views


router = DefaultRouter()
router.register(r'account', views.AccountViewSet)
router.register(r'order', views.OrderViewSet)
router.register(r'trade', views.TradeViewSet)
router.register(r'price', views.PriceViewSet)

urlpatterns = [
	path('', include(router.urls)),
	path('login/', views.LoginView.as_view()),
	path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
