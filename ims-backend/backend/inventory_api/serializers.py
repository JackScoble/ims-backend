from rest_framework import serializers
from .models import Category, InventoryItem, StockAudit
from django.contrib.auth.models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        # create_user automatically hashes the password! (Crucial for enterprise security)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class StockAuditSerializer(serializers.ModelSerializer):
    # We want to display the user's username rather than just their ID number
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = StockAudit
        fields = ['id', 'item', 'user', 'quantity_changed', 'reason', 'timestamp']

class InventoryItemSerializer(serializers.ModelSerializer):
    # This embeds the category details directly into the item JSON
    category_name = serializers.ReadOnlyField(source='category.name')
    # This brings in our audit history so we can see it when viewing an item
    audit_logs = StockAuditSerializer(many=True, read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'name', 'sku', 'description', 'quantity', 
            'category', 'category_name', 'created_at', 'updated_at', 
            'owner', 'audit_logs'
        ]
        # We make owner read-only so people can't re-assign who owns the item
        read_only_fields = ['owner', 'created_at', 'updated_at']