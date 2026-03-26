from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, InventoryItemViewSet, StockAuditViewSet, RegisterUserView, UserViewSet, DailyStockSnapshotListView, UserProfileView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'items', InventoryItemViewSet)
router.register(r'audit', StockAuditViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('snapshots/', DailyStockSnapshotListView.as_view(), name='stock-snapshots'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('', include(router.urls)),
]