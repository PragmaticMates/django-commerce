# Generated by Django 2.2.4 on 2020-07-23 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0029_order_reminder_sent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('AWAITING_PAYMENT', 'Awaiting Payment'), ('PAYMENT_RECEIVED', 'Payment received'), ('PROCESSING', 'Processing'), ('AWAITING_FULFILLMENT', 'Awaiting Fulfillment'), ('AWAITING_SHIPMENT', 'Awaiting Shipment'), ('AWAITING_PICKUP', 'Awaiting Pickup'), ('PARTIALLY_SHIPPED', 'Partially Shipped'), ('SHIPPED', 'Shipped'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'), ('DECLINED', 'Declined'), ('REFUNDED', 'Refunded'), ('PARTIALLY_REFUNDED', 'Partially Refunded'), ('DISPUTED', 'Disputed'), ('ON_HOLD', 'On hold')], max_length=20, verbose_name='status'),
        ),
    ]