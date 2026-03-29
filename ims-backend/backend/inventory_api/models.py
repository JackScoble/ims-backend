"""
Database models for the Inventory Management System.
Defines the schema for inventory items, categorization, user profiles,
and audit logging.
"""

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
    """
    Represents a grouping category for inventory items.

    Attributes:
        name (str): The unique display name of the category.
        description (str): Optional text describing the category contents.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    """
    Represents a single unique product or material within the inventory.

    Attributes:
        name (str): The display name of the item.
        sku (str): Unique Stock Keeping Unit identifier.
        description (str): Detailed text regarding the item.
        quantity (int): Current number of physical units in stock.
        price (Decimal): The monetary value of a single unit.
        low_stock_threshold (int): The quantity at which low-stock alerts are triggered.
        category (Category): The grouping this item belongs to.
        image (ImageFile): Optional visual representation of the item.
        created_at (datetime): Timestamp of item creation.
        updated_at (datetime): Timestamp of the last modification.
        owner (User): The user responsible for this specific item.
    """
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
    """
    Records a historical log of system actions for accountability and tracking.

    Attributes:
        user (User): The system user who performed the action.
        username (str): Captured username for historical integrity if the User is deleted.
        timestamp (datetime): When the action occurred.
        object_type (str): The entity affected ('ITEM', 'CATEGORY', 'USER').
        object_id (int): The primary key of the affected entity.
        object_name (str): Human-readable identifier of the entity.
        action (str): The type of operation performed ('CREATE', 'UPDATE', 'DELETE').
        description (str): A detailed breakdown of the exact fields changed.
        fields_changed_count (int): The total number of attributes modified in this action.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=150, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    object_type = models.CharField(max_length=50, default="UNKNOWN")
    object_id = models.PositiveIntegerField(null=True)
    object_name = models.CharField(max_length=255, blank=True)
    
    action = models.CharField(max_length=20)
    description = models.TextField(default="")
    fields_changed_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.action} on {self.object_type} by {self.username}"

class DailyStockSnapshot(models.Model):
    """
    Captures a point-in-time calculation of total inventory value for analytical charting.

    Attributes:
        date (date): The specific calendar day the snapshot represents.
        total_value (Decimal): The aggregate monetary value of all inventory on this date.
    """
    date = models.DateField(default=timezone.now, unique=True)
    total_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['date'] 

    def __str__(self):
        return f"{self.date} - £{self.total_value}"

class UserProfile(models.Model):
    """
    Extended user attributes that expand upon the default Django User model.

    Attributes:
        user (User): The base Django authentication record.
        profile_image (ImageFile): Avatar uploaded by the user.
        department (str): The organizational unit the user belongs to.
        job_title (str): The user's specific role.
        theme_preference (str): UI color scheme preference ('light', 'dark', 'system').
    """
    THEME_CHOICES = (
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System Default'),
    )

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

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to automatically generate a UserProfile when a new User is registered.
    """
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal handler to ensure the related UserProfile saves when the User object updates.
    """
    instance.profile.save()

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Signal handler that triggers upon password reset token generation.
    Constructs a dynamic frontend URL and dispatches the recovery email.

    Args:
        reset_password_token (ResetPasswordToken): The generated secure token instance.
    """
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
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
    """
    Represents a transaction reducing the stock quantity of a specific item.

    Attributes:
        item (InventoryItem): The product being ordered/removed.
        quantity_ordered (int): The volume of units removed from stock.
        processed_by (User): The user who executed the order.
        created_at (datetime): Timestamp of the order transaction.
    """
    item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE, related_name='orders')
    quantity_ordered = models.PositiveIntegerField()
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order: {self.quantity_ordered}x {self.item.name}"