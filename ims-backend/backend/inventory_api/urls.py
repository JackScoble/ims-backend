from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, InventoryItemViewSet, StockAuditViewSet

# The router automatically creates all the CRUD routes for us!
router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'items', InventoryItemViewSet)
router.register(r'audit', StockAuditViewSet)

urlpatterns = [
    path('', include(router.urls)),
]