"""
API view controllers for the Inventory Management System.
Handles business logic, request routing, and automatic audit logging injections.
"""

from rest_framework import viewsets, permissions, generics, exceptions, status
from .models import Category, InventoryItem, StockAudit, DailyStockSnapshot, Order
from .serializers import *
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
import os

# --- AUDIT ENGINE ---
def log_complex_audit(user, action, obj_type, instance, validated_data=None):
    """
    Calculates differences between database states and saves a detailed audit record.

    Args:
        user (User): The user performing the action.
        action (str): The type of action ('CREATE', 'UPDATE', 'DELETE').
        obj_type (str): The system entity type ('ITEM', 'CATEGORY', 'USER', 'ORDER').
        instance (Model): The database instance being manipulated.
        validated_data (dict, optional): The incoming new data payload. Defaults to None.
    """
    description = ""
    changes_count = 0
    obj_name = str(instance)
    obj_id = instance.id

    if action == 'CREATE':
        description = f"Created new {obj_type}."
        changes_count = len(validated_data.keys()) if validated_data else 0
    
    elif action == 'DELETE':
        description = f"Deleted {obj_type}: {obj_name} (ID: {obj_id})"
        changes_count = 0
        
    elif action == 'UPDATE' and validated_data:
        diffs = []
        for field, new_value in validated_data.items():
            old_value = getattr(instance, field)
            
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
    """
    API endpoint for registering new user accounts.
    Open to unauthenticated requests.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        log_complex_audit(user, 'CREATE', 'USER', user, serializer.validated_data)

class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for managing Inventory Categories.
    Automatically logs Create, Update, and Delete operations to the audit trail.
    """
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

def send_low_stock_email(item):
    """
    Constructs and dispatches a notification email when an item breaches its low-stock threshold.

    Args:
        item (InventoryItem): The specific inventory instance that is running low.
    """
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

    subject = f"IMS Pro: Low Stock Alert for {item.name}"
    
    message = (
        f"Hello,\n\n"
        f"This is an automated alert. Your inventory for '{item.name}' "
        f"has dropped to {item.quantity}, which is at or below your custom "
        f"warning threshold of {item.low_stock_threshold}.\n\n"
        f"Please log in to IMS Pro to restock soon: {frontend_url}"
    )

    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #d73a49; border-bottom: 2px solid #eee; padding-bottom: 10px;">⚠️ Low Stock Alert</h2>
            <p>Hello,</p>
            <p>This is an automated alert. Your inventory for <strong>'{item.name}'</strong> 
            has dropped to <strong>{item.quantity}</strong>, which is at or below your custom 
            warning threshold of {item.low_stock_threshold}.</p>
            
            <p>Please log in to your dashboard to restock soon!</p>
            
            <div style="margin: 30px 0;">
                <a href="{frontend_url}" 
                   style="background-color: #2196F3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                   Go to IMS Pro
                </a>
            </div>
            
            <p style="font-size: 12px; color: #777; border-top: 1px solid #eee; padding-top: 10px;">
                If the button doesn't work, copy and paste this link into your browser: <br>
                {frontend_url}
            </p>
        </body>
    </html>
    """
    
    recipient_email = item.owner.email 

    if recipient_email:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
            html_message=html_message
        )

class InventoryItemViewSet(viewsets.ModelViewSet):
    """
    Core ViewSet for full CRUD capabilities on Inventory items.
    Enforces ownership permissions and intercepts saves to monitor low-stock thresholds.
    """
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves a single inventory item and appends its specific audit history to the payload.
        """
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
        """
        Intercepts item updates to verify changes in quantity against low-stock thresholds.
        """
        old_instance = self.get_object()
        old_quantity = old_instance.quantity

        item = serializer.save()
        new_quantity = item.quantity
        threshold = item.low_stock_threshold

        log_complex_audit(self.request.user, 'UPDATE', 'ITEM', old_instance, serializer.validated_data)

        if old_quantity > threshold and new_quantity <= threshold:
            send_low_stock_email(item)

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise exceptions.PermissionDenied("Ownership required for deletion.")
        
        log_complex_audit(self.request.user, 'DELETE', 'ITEM', instance)
        instance.delete()

class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for processing transactions.
    Automatically deducts order quantities from the parent InventoryItem stock.
    """
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Executes the order, updates related inventory stock, and logs multiple audit entries.
        """
        order = serializer.save(processed_by=self.request.user)
        item = order.item
        
        log_complex_audit(
            user=self.request.user,
            action='CREATE',
            obj_type='ORDER',
            instance=order,
            validated_data=serializer.validated_data
        )
        
        old_quantity = item.quantity
        new_quantity = item.quantity - order.quantity_ordered
        
        log_complex_audit(
            user=self.request.user, 
            action='UPDATE', 
            obj_type='ITEM', 
            instance=item, 
            validated_data={'quantity': new_quantity} 
        )

        item.quantity = new_quantity
        item.save()

        if old_quantity > item.low_stock_threshold and new_quantity <= item.low_stock_threshold:
            send_low_stock_email(item)

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet to handle User account updates and deletions with enforced audit logging.
    """
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
    """
    Read-only endpoint exposing the historical system audit trail.
    """
    queryset = StockAudit.objects.all().order_by('-timestamp')
    serializer_class = StockAuditSerializer
    permission_classes = [IsAuthenticated]

class DailyStockSnapshotListView(generics.ListAPIView):
    """
    Endpoint for retrieving time-series inventory value data for analytical charting.
    """
    queryset = DailyStockSnapshot.objects.all()
    serializer_class = DailyStockSnapshotSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Endpoint for a user to retrieve and modify their own extended profile attributes.
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class PasswordChangeView(APIView):
    """
    Dedicated endpoint for authenticated password modification.
    Enforces Django's native password validation rules and validates the old password.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not user.check_password(old_password):
            return Response(
                {"error": "Your current password was entered incorrectly. Please try again."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {"error": e.messages[0]}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password updated successfully!"}, 
            status=status.HTTP_200_OK
        )