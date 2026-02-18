from rest_framework import viewsets, permissions
from .models import Category, InventoryItem, StockAudit
from .serializers import CategorySerializer, InventoryItemSerializer, StockAuditSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # We will restrict this later, but for now allow anyone to view/edit
    permission_classes = [permissions.AllowAny] 

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    # This is an enterprise feature: Automatically set the owner to the logged-in user!
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class StockAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    We use ReadOnlyModelViewSet because audit logs should NEVER be manually 
    created, updated, or deleted via standard API calls. They are an unchangeable history.
    """
    queryset = StockAudit.objects.all().order_by('-timestamp')
    serializer_class = StockAuditSerializer
    permission_classes = [permissions.IsAuthenticated]