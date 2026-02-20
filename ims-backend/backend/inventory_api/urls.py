from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Added UserViewSet to the import list
from .views import CategoryViewSet, InventoryItemViewSet, StockAuditViewSet, RegisterUserView, UserViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'items', InventoryItemViewSet)
router.register(r'audit', StockAuditViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('', include(router.urls)),
]