from rest_framework import viewsets, permissions, generics, exceptions, status
from .models import Category, InventoryItem, StockAudit, DailyStockSnapshot
from .serializers import *
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# --- AUDIT ENGINE ---
def log_complex_audit(user, action, obj_type, instance, validated_data=None):
    """
    Calculates differences and saves a detailed audit record.
    """
    description = ""
    changes_count = 0
    obj_name = str(instance)
    obj_id = instance.id

    if action == 'CREATE':
        description = f"Created new {obj_type}."
        # Count fields provided during creation
        changes_count = len(validated_data.keys()) if validated_data else 0
    
    elif action == 'DELETE':
        description = f"Deleted {obj_type}: {obj_name} (ID: {obj_id})"
        changes_count = 0
        
    elif action == 'UPDATE' and validated_data:
        diffs = []
        for field, new_value in validated_data.items():
            # Get the current value from the database before the save
            old_value = getattr(instance, field)
            
            # Simple comparison (handles strings, ints, and objects)
            if str(old_value) != str(new_value):
                diffs.append(f"{field}: {old_value} → {new_value}")
                changes_count += 1
        
        description = " | ".join(diffs) if diffs else "Update triggered, but no values changed."

    StockAudit.objects.create(
        user=user,
        username=user.username if user else "Anonymous",
        object_type=obj_type,
        object_id=obj_id,
        object_name=obj_name,
        action=action,
        description=description,
        fields_changed_count=changes_count
    )

# --- VIEWS ---

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        log_complex_audit(user, 'CREATE', 'USER', user, serializer.validated_data)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        cat = serializer.save()
        log_complex_audit(self.request.user, 'CREATE', 'CATEGORY', cat, serializer.validated_data)

    def perform_update(self, serializer):
        old_instance = self.get_object()
        cat = serializer.save()
        log_complex_audit(self.request.user, 'UPDATE', 'CATEGORY', old_instance, serializer.validated_data)

    def perform_destroy(self, instance):
        log_complex_audit(self.request.user, 'DELETE', 'CATEGORY', instance)
        instance.delete()

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        audit_logs = StockAudit.objects.filter(
            object_id=instance.id,
            object_type='ITEM'
        ).order_by('-timestamp')
        
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['audit_logs'] = StockAuditSerializer(audit_logs, many=True).data
        return Response(data)

    def perform_create(self, serializer):
        item = serializer.save(owner=self.request.user)
        log_complex_audit(self.request.user, 'CREATE', 'ITEM', item, serializer.validated_data)

    def perform_update(self, serializer):
        old_instance = self.get_object()
        item = serializer.save()
        log_complex_audit(self.request.user, 'UPDATE', 'ITEM', old_instance, serializer.validated_data)

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise exceptions.PermissionDenied("Ownership required for deletion.")
        
        log_complex_audit(self.request.user, 'DELETE', 'ITEM', instance)
        instance.delete()

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet to handle User account updates/deletes with auditing"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        old_instance = self.get_object()
        user = serializer.save()
        log_complex_audit(self.request.user, 'UPDATE', 'USER', old_instance, serializer.validated_data)

    def perform_destroy(self, instance):
        log_complex_audit(self.request.user, 'DELETE', 'USER', instance)
        instance.delete()

class StockAuditViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockAudit.objects.all().order_by('-timestamp')
    serializer_class = StockAuditSerializer
    permission_classes = [IsAuthenticated]

class DailyStockSnapshotListView(generics.ListAPIView):
    queryset = DailyStockSnapshot.objects.all()
    serializer_class = DailyStockSnapshotSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class PasswordChangeView(APIView):
    """
    An endpoint for changing password.
    Requires the user to be authenticated and provide their old password.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        # 1. Verify the old password
        if not user.check_password(old_password):
            return Response(
                {"error": "Your current password was entered incorrectly. Please try again."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Validate the new password using Django's rules
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {"error": e.messages[0]}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Save the new password
        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password updated successfully!"}, 
            status=status.HTTP_200_OK
        )