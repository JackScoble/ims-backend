from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
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

class DailyStockSnapshot(models.Model):
    date = models.DateField(default=timezone.now, unique=True)
    total_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['date'] # Ensures the chart always reads left-to-right by date

    def __str__(self):
        return f"{self.date} - £{self.total_value}"

class UserProfile(models.Model):
    # Links directly to the built-in User table
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# --- DJANGO SIGNALS ---
# This automatically creates a UserProfile whenever a new User registers
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# This automatically saves the UserProfile whenever the User is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()