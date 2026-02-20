from rest_framework import serializers
from .models import Category, InventoryItem, StockAudit
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

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class StockAuditSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    item_name = serializers.ReadOnlyField(source='item.name')
    
    class Meta:
        model = StockAudit
        fields = [
            'id', 'user', 'username', 'timestamp', 
            'object_type', 'object_id', 'object_name', 
            'action', 'description', 'fields_changed_count'
        ]

class InventoryItemSerializer(serializers.ModelSerializer):
    # This embeds the category details directly into the item JSON
    category_name = serializers.ReadOnlyField(source='category.name')

    owner_name = serializers.ReadOnlyField(source='owner.username')
    owner_email = serializers.ReadOnlyField(source='owner.email')

    # This brings in our audit history so we can see it when viewing an item
    audit_logs = StockAuditSerializer(many=True, read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'name', 'sku', 'description', 'quantity', 
            'category', 'category_name', 'image', 'created_at', 'updated_at', 
            'owner', 'owner_name', 'owner_email', 'audit_logs'
        ]
        # We make owner read-only so people can't re-assign who owns the item
        read_only_fields = ['owner', 'owner_name', 'owner_email', 'created_at', 'updated_at']