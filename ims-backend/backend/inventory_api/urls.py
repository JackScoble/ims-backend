"""
URL Configuration for the Inventory Management System API.
Maps API endpoints to their corresponding ViewSets and generic views.
Utilizes DRF's DefaultRouter for automatic standard CRUD routing.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, InventoryItemViewSet, StockAuditViewSet, RegisterUserView, UserViewSet, DailyStockSnapshotListView, UserProfileView, PasswordChangeView, OrderViewSet

# --- ROUTER SETUP ---
# Automatically generates RESTful URL patterns for standard ViewSets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'items', InventoryItemViewSet)
router.register(r'audit', StockAuditViewSet)
router.register(r'users', UserViewSet)
router.register(r'orders', OrderViewSet)

# --- URL PATTERNS ---
urlpatterns = [
    # Custom/Specific Endpoints
    path('register/', RegisterUserView.as_view(), name='register'),
    path('snapshots/', DailyStockSnapshotListView.as_view(), name='stock-snapshots'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Authentication & Password Management
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('password_change/', PasswordChangeView.as_view(), name='password_change'),
    
    # Router Endpoints (must be included at the end or with a specific prefix)
    path('', include(router.urls)),
]