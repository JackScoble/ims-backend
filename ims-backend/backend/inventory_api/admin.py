from django.contrib import admin
from .models import Category, InventoryItem, StockAudit

admin.site.register(Category)
admin.site.register(InventoryItem)
admin.site.register(StockAudit)