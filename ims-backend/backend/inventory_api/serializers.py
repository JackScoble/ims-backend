from rest_framework import serializers
from .models import Category, InventoryItem, StockAudit, DailyStockSnapshot, UserProfile, Order
from django.contrib.auth.models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'], 
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'department', 'job_title']

class UserUpdateSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['username']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        profile = instance.profile
        profile.department = profile_data.get('department', profile.department)
        profile.job_title = profile_data.get('job_title', profile.job_title)
        
        if 'profile_image' in profile_data:
            profile.profile_image = profile_data['profile_image']
            
        profile.save()

        return instance

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class StockAuditSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = StockAudit
        fields = [
            'id', 'user', 'username', 'timestamp', 
            'object_type', 'object_id', 'object_name', 
            'action', 'description', 'fields_changed_count'
        ]

class InventoryItemSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = DailyStockSnapshot
        fields = ['date', 'total_value']

class OrderSerializer(serializers.ModelSerializer):
    item_name = serializers.ReadOnlyField(source='item.name')
    
    class Meta:
        model = Order
        fields = ['id', 'item', 'item_name', 'quantity_ordered', 'processed_by', 'created_at']
        read_only_fields = ['processed_by', 'created_at']

    def validate(self, data):
        if data['quantity_ordered'] <= 0:
            raise serializers.ValidationError({"quantity_ordered": "Order quantity must be at least 1."})
        
        if data['item'].quantity < data['quantity_ordered']:
            raise serializers.ValidationError({
                "quantity_ordered": f"Not enough stock! Only {data['item'].quantity} left in inventory."
            })
        
        return data