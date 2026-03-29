from django.test import TestCase
from django.contrib.auth.models import User
from inventory_api.models import Category, InventoryItem, UserProfile, Order

class ModelUnitTests(TestCase):
    def setUp(self):
        # Create a test user (which should trigger the UserProfile signal)
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
        """Domain Logic: Ensure the Django post_save signal creates a UserProfile automatically."""
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())
        self.assertEqual(self.user.profile.theme_preference, 'system')

    def test_inventory_item_string_representation(self):
        """Domain Logic: Ensure the __str__ method formats correctly."""
        self.assertEqual(str(self.item), "Test Laptop (SKU: LAP-001)")

    def test_order_string_representation(self):
        """Domain Logic: Ensure Order string formats correctly."""
        order = Order.objects.create(item=self.item, quantity_ordered=5, processed_by=self.user)
        self.assertEqual(str(order), "Order: 5x Test Laptop")