from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.core import mail
from inventory_api.models import Category, InventoryItem, StockAudit

class APIWorkflowTests(APITestCase):
    def setUp(self):
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
        """Workflow: Only the owner can delete an item. Others get PermissionDenied."""
        self.client.force_authenticate(user=self.other_user) # Switch to non-owner
        url = f"{self.items_url}{self.item.id}/"
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(InventoryItem.objects.filter(id=self.item.id).exists())

    def test_order_creation_deducts_stock_and_triggers_audit(self):
        """Workflow: Creating an order must deduct stock and write to the audit log."""
        payload = {
            "item": self.item.id,
            "quantity_ordered": 5
        }
        response = self.client.post(self.orders_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify stock was deducted
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 15)
        
        # Verify Audit Log was created for the Order AND the Item Update
        audit_exists = StockAudit.objects.filter(action='CREATE', object_type='ORDER').exists()
        self.assertTrue(audit_exists)

    def test_low_stock_email_triggered_on_order(self):
        """Enterprise Requirement: Placing a large order that drops stock below threshold must send an email."""
        # Stock is 20, threshold is 5. Ordering 16 drops it to 4.
        payload = {
            "item": self.item.id,
            "quantity_ordered": 16
        }
        response = self.client.post(self.orders_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check Django's in-memory mail outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"IMS Pro: Low Stock Alert for {self.item.name}")
        self.assertIn("has dropped to 4", mail.outbox[0].body)

    def test_cannot_create_negative_quantity(self):
        """Edge Case: Ensure the API rejects negative stock quantities."""
        payload = {
            "name": "Ghost Item",
            "sku": "GHOST-001",
            "quantity": -10, 
            "price": 10.00,
            "category": self.category.id
        }
        response = self.client.post(self.items_url, payload)
        # Even if it returns 201, this test will tell us if your model constraints are working
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, "API allowed negative quantity!")

    def test_order_exceeding_inventory_fails(self):
        """Domain Logic: Ensure users cannot order more than what is in stock."""
        # Item has 20 (from setUp).
        payload = {"item": self.item.id, "quantity_ordered": 500}
        response = self.client.post(self.orders_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Verify stock DID NOT change
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 20)