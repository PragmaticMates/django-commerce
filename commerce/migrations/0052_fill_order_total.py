from commerce.models import Order
from django.db import migrations
from django.db.migrations import RunPython


def fill_order_total_field(*args, **kwargs):

    orders_without_total = Order.objects.filter(total=0)

    for order in orders_without_total:
        order.total = order.calculate_total()

    Order.objects.bulk_update(orders_without_total, fields=['total'])


class Migration(migrations.Migration):
    dependencies = [
        ('commerce', '0051_order_total'),
    ]

    operations = [
        RunPython(fill_order_total_field, lambda *args, **kwargs: None)
    ]
