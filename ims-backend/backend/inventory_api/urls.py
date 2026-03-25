from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, InventoryItemViewSet, StockAuditViewSet, RegisterUserView, UserViewSet, DailyStockSnapshotListView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'items', InventoryItemViewSet)
router.register(r'audit', StockAuditViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('snapshots/', DailyStockSnapshotListView.as_view(), name='stock-snapshots'),
    path('', include(router.urls)),
]