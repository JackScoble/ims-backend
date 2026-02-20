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
    quantity = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items')
    image = models.ImageField(upload_to='inventory_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_items')

    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"

class StockAudit(models.Model):
    # Who changed it
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=150, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # What was changed
    object_type = models.CharField(max_length=50, default="UNKNOWN") # 'ITEM', 'CATEGORY', 'USER'
    object_id = models.PositiveIntegerField(null=True)
    object_name = models.CharField(max_length=255, blank=True) # SKU, Name, or Username
    
    # Action details
    action = models.CharField(max_length=20) # 'CREATE', 'UPDATE', 'DELETE'
    description = models.TextField(default="")
    fields_changed_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.action} on {self.object_type} by {self.username}"