"""
API Serializers for the Inventory Management System.
Responsible for converting complex querysets and model instances into native Python
datatypes that can be easily rendered into JSON, as well as validating incoming data.
"""

from rest_framework import serializers
from .models import Category, InventoryItem, StockAudit, DailyStockSnapshot, UserProfile, Order
from django.contrib.auth.models import User
from django.utils import timezone

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new user accounts.
    Explicitly makes the password write-only so it is never exposed in API responses.
    """
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email', 'password']

    def create(self, validated_data):
        """
        Overrides the default create method to use Django's create_user utility,
        which automatically hashes the password before saving.
        """
        user = User.objects.create_user(
            username=validated_data['email'], 
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the extended UserProfile attributes.
    Usually nested within the UserUpdateSerializer.
    """
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'department', 'job_title', 'theme_preference']

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for user accounts.
    Handles nested updates for the related UserProfile and computes dynamic
    statistics (items added, daily edits) on the fly.
    """
    profile = UserProfileSerializer()
    
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    
    items_added = serializers.SerializerMethodField()
    edits_today = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'profile',
            'date_joined', 'last_login', 'items_added', 'edits_today', 'role'
        ]
        read_only_fields = ['username', 'date_joined', 'last_login']

    def get_items_added(self, obj):
        return obj.inventory_items.count()

    def get_edits_today(self, obj):
        today = timezone.now().date()
        return StockAudit.objects.filter(user=obj, timestamp__date=today).count()

    def get_role(self, obj):
        if obj.is_superuser:
            return "Administrator"
        return ""

    def update(self, instance, validated_data):
        """
        Custom update logic to handle writing to both the User model 
        and the nested UserProfile model simultaneously.
        """
        profile_data = validated_data.pop('profile', {})
        
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        profile = instance.profile
        profile.department = profile_data.get('department', profile.department)
        profile.job_title = profile_data.get('job_title', profile.job_title)
        profile.theme_preference = profile_data.get('theme_preference', profile.theme_preference)
        
        if 'profile_image' in profile_data:
            profile.profile_image = profile_data['profile_image']
            
        profile.save()

        return instance

class CategorySerializer(serializers.ModelSerializer):
    """
    Standard serializer for inventory categories.
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class StockAuditSerializer(serializers.ModelSerializer):
    """
    Serializer for system audit logs.
    Pulls the human-readable username from the related User model.
    """
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = StockAudit
        fields = [
            'id', 'user', 'username', 'timestamp', 
            'object_type', 'object_id', 'object_name', 
            'action', 'description', 'fields_changed_count'
        ]

class InventoryItemSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for Inventory Items.
    Flattens related fields (category name, owner info) for easier frontend consumption
    and nests the item's specific audit history.
    """
    category_name = serializers.ReadOnlyField(source='category.name')

    owner_name = serializers.ReadOnlyField(source='owner.username')
    owner_email = serializers.ReadOnlyField(source='owner.email')

    audit_logs = StockAuditSerializer(many=True, read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'name', 'sku', 'description', 'quantity', 
            'price', 'low_stock_threshold', 'category', 'category_name', 'image', 'created_at', 
            'updated_at', 'owner', 'owner_name', 'owner_email', 'audit_logs'
        ]
        read_only_fields = ['owner', 'owner_name', 'owner_email', 'created_at', 'updated_at']

class DailyStockSnapshotSerializer(serializers.ModelSerializer):
    """
    Serializer for historical inventory value data points.
    """
    class Meta:
        model = DailyStockSnapshot
        fields = ['date', 'total_value']

class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for inventory outbound orders.
    Validates stock availability before allowing an order to process.
    """
    item_name = serializers.ReadOnlyField(source='item.name')
    processed_by_username = serializers.ReadOnlyField(source='processed_by.username')
    
    class Meta:
        model = Order
        fields = ['id', 'item', 'item_name', 'quantity_ordered', 'processed_by', 'processed_by_username', 'created_at']
        read_only_fields = ['processed_by', 'created_at']

    def validate(self, data):
        """
        Business logic validation layer.
        Ensures order quantities are valid and that sufficient stock exists.
        """
        if data['quantity_ordered'] <= 0:
            raise serializers.ValidationError({"quantity_ordered": "Order quantity must be at least 1."})
        
        if data['item'].quantity < data['quantity_ordered']:
            raise serializers.ValidationError({
                "quantity_ordered": f"Not enough stock! Only {data['item'].quantity} left in inventory."
            })
        
        return data