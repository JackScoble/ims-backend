from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, InventoryItemViewSet, StockAuditViewSet, RegisterUserView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'items', InventoryItemViewSet)
router.register(r'audit', StockAuditViewSet)

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('', include(router.urls)),
]