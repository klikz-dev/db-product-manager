from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from misc.views import ConfigViewSet
from mysql.views import AddressViewSet, CustomerViewSet, ImageViewSet
from shopify.views import LineItemViewSet, OrderViewSet, ProductViewSet, VariantViewSet

from . import views

router = routers.DefaultRouter()
router.register(r'orders', OrderViewSet)
router.register(r'line-items', LineItemViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'addresses', AddressViewSet)
router.register(r'images', ImageViewSet)
router.register(r'products', ProductViewSet)
router.register(r'variants', VariantViewSet)
router.register(r'config', ConfigViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/dj-rest-auth/', include('dj_rest_auth.urls'))
]
