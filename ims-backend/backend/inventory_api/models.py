from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created
import os

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
    low_stock_threshold = models.IntegerField(default=5)
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
    THEME_CHOICES = (
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System Default'),
    )

    # Links directly to the built-in User table
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    
    theme_preference = models.CharField(
        max_length=10, 
        choices=THEME_CHOICES, 
        default='system'
    )

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

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    """
    # Pull the frontend URL from the environment, fallback to localhost just in case
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    
    # Construct the exact URL for your React app
    reset_url = f"{frontend_url}/reset-password?token={reset_password_token.key}"

    print(f"\n\n--- PASSWORD RESET LINK ---\n{reset_url}\n---------------------------\n\n")
    
    email_html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>IMS Pro - Password Reset</h2>
            <p>Hello {reset_password_token.user.username},</p>
            <p>You recently requested to reset your password for your IMS Pro account. Click the button below to reset it:</p>
            <a href="{reset_url}" style="display: inline-block; padding: 10px 20px; background-color: #8884d8; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Reset My Password</a>
            <p style="margin-top: 20px; font-size: 12px; color: #777;">If you did not request a password reset, please ignore this email.</p>
        </body>
    </html>
    """

    send_mail(
        subject="IMS Pro - Password Reset Request",
        message=f"Please use this link to reset your password: {reset_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reset_password_token.user.email],
        html_message=email_html_message,
        fail_silently=False,
    )

class Order(models.Model):
    item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE, related_name='orders')
    quantity_ordered = models.PositiveIntegerField()
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order: {self.quantity_ordered}x {self.item.name}"