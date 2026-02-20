from rest_framework import viewsets, permissions, generics
from .models import Category, InventoryItem, StockAudit
from .serializers import UserRegistrationSerializer, CategorySerializer, InventoryItemSerializer, StockAuditSerializer
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny] # Anyone can register
    serializer_class = UserRegistrationSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny] 

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Automatically set the owner to the logged-in user
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        # Check if the person deleting is the owner
        if instance.owner != self.request.user:
            raise exceptions.PermissionDenied("You do not have permission to delete this item.")
        instance.delete()

class StockAuditViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockAudit.objects.all().order_by('-timestamp')
    serializer_class = StockAuditSerializer
    permission_classes = [permissions.IsAuthenticated]