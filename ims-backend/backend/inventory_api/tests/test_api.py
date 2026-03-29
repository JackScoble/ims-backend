"""
Integration and Workflow tests for the Inventory Management System API.
Ensures that business logic, permissions, and automated triggers (like emails
and audit logs) function correctly across complex multi-step interactions.
"""

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.core import mail
from inventory_api.models import Category, InventoryItem, StockAudit

class APIWorkflowTests(APITestCase):
    """
    Test suite validating the core operational workflows of the inventory API.
    """
    
    def setUp(self):
        """
        Initializes the test database with standard mock data before each test runs.
        Creates two distinct users (an owner and a non-owner), a category, and a base inventory item.
        Authenticates the client as the primary owner.
        """
        self.user = User.objects.create_user(username='manager', email='manager@test.com', password='password123')
        self.other_user = User.objects.create_user(username='hacker', password='password123')
        
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name='Furniture')
        self.item = InventoryItem.objects.create(
            name='Office Chair',
            sku='CHR-001',
            quantity=20,
            low_stock_threshold=5,
            category=self.category,
            owner=self.user
        )
        
        self.items_url = '/api/items/'
        self.orders_url = '/api/orders/'

    def test_ownership_required_for_deletion(self):
        """
        Validates endpoint authorization logic.
        Ensures that a user who does not own an inventory item cannot delete it, 
        verifying that a 403 Forbidden is returned and the item remains in the database.
        """
        self.client.force_authenticate(user=self.other_user)
        url = f"{self.items_url}{self.item.id}/"
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(InventoryItem.objects.filter(id=self.item.id).exists())

    def test_order_creation_deducts_stock_and_triggers_audit(self):
        """
        Validates the standard order fulfillment workflow.
        Ensures that processing an order successfully deducts the exact ordered quantity
        from the related inventory item and automatically generates a StockAudit record.
        """
        payload = {
            "item": self.item.id,
            "quantity_ordered": 5
        }
        response = self.client.post(self.orders_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 15)
        
        audit_exists = StockAudit.objects.filter(action='CREATE', object_type='ORDER').exists()
        self.assertTrue(audit_exists)

    def test_low_stock_email_triggered_on_order(self):
        """
        Validates automated notification triggers.
        Ensures that if an order reduces inventory stock to or below the item's
        custom 'low_stock_threshold', an alert email is dispatched to the item's owner.
        """
        payload = {
            "item": self.item.id,
            "quantity_ordered": 16
        }
        response = self.client.post(self.orders_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"IMS Pro: Low Stock Alert for {self.item.name}")
        self.assertIn("has dropped to 4", mail.outbox[0].body)

    def test_cannot_create_negative_quantity(self):
        """
        Validates data integrity constraints on the InventoryItem model.
        Ensures that the API properly rejects POST requests attempting to create
        stock with a negative quantity.
        """
        payload = {
            "name": "Ghost Item",
            "sku": "GHOST-001",
            "quantity": -10, 
            "price": 10.00,
            "category": self.category.id
        }
        response = self.client.post(self.items_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, "API allowed negative quantity!")

    def test_order_exceeding_inventory_fails(self):
        """
        Validates business logic constraints during order creation.
        Ensures that an order requesting a higher quantity than the available stock
        is rejected (400 Bad Request) and that the existing stock level remains unchanged.
        """
        payload = {"item": self.item.id, "quantity_ordered": 500}
        response = self.client.post(self.orders_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 20)