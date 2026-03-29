"""
Unit tests for the Inventory Management System database models.
Validates internal Django ORM behavior, signal triggers, and object representations.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from inventory_api.models import Category, InventoryItem, UserProfile, Order

class ModelUnitTests(TestCase):
    """
    Test suite validating the structural integrity and logic of database models.
    """
    
    def setUp(self):
        """
        Populates the test database with a foundational hierarchy:
        A User, a Category, and an InventoryItem assigned to that User.
        """
        self.user = User.objects.create_user(username='testadmin', password='testpassword123')
        self.category = Category.objects.create(name='Electronics', description='Tech gear')
        self.item = InventoryItem.objects.create(
            name='Test Laptop',
            sku='LAP-001',
            quantity=50,
            price=1000.00,
            low_stock_threshold=10,
            category=self.category,
            owner=self.user
        )

    def test_user_profile_created_on_user_creation(self):
        """
        Validates the Django post_save signal attached to the User model.
        Ensures that whenever a new Django User is created, an associated UserProfile
        is automatically generated with system default settings.
        """
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())
        self.assertEqual(self.user.profile.theme_preference, 'system')

    def test_inventory_item_string_representation(self):
        """
        Validates the __str__ magic method of the InventoryItem model.
        Ensures instances are represented in a human-readable format for the Django Admin
        and logging outputs.
        """
        self.assertEqual(str(self.item), "Test Laptop (SKU: LAP-001)")

    def test_order_string_representation(self):
        """
        Validates the __str__ magic method of the Order model.
        Ensures order transactions clearly display quantity and item names in logs.
        """
        order = Order.objects.create(item=self.item, quantity_ordered=5, processed_by=self.user)
        self.assertEqual(str(order), "Order: 5x Test Laptop")