from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import F, Sum, DecimalField
from inventory_api.models import InventoryItem, DailyStockSnapshot 

class Command(BaseCommand):
    help = 'Calculates the total stock value and saves a daily snapshot'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        
        # Calculate total value: sum of (quantity * price) for all items
        total = InventoryItem.objects.aggregate(
            total_value=Sum(
                F('quantity') * F('price'),
                output_field=DecimalField()
            )
        )['total_value'] or 0.00

        # Update or create today's snapshot
        snapshot, created = DailyStockSnapshot.objects.update_or_create(
            date=today,
            defaults={'total_value': total}
        )

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f'{action} snapshot for {today}: £{total}'))