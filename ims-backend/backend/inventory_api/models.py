from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=0) # Prevents negative stock values natively
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items')
    image = models.ImageField(upload_to='inventory_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_items')

    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"

class StockAudit(models.Model):
    """Tracks every time stock is added or removed (Audit History)"""
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    quantity_changed = models.IntegerField() # e.g., +50 or -10
    reason = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.name} | Change: {self.quantity_changed} | Date: {self.timestamp}"