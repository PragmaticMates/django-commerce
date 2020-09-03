import django.dispatch
from django.db.models.signals import pre_save
from django.dispatch import receiver
from invoicing.models import Invoice

from commerce.models import Order, Cart
from commerce.tasks import notify_about_new_order, notify_about_changed_order_status
from pragmatic.signals import apm_custom_context, SignalsHelper

checkout_finished = django.dispatch.Signal(providing_args=["order"])
cart_updated = django.dispatch.Signal(providing_args=["item"])


@receiver(checkout_finished, sender=Cart)
@apm_custom_context('signals')
def order_created(sender, order, **kwargs):
    # only if order status == payment received? (NO!, because we need to create invoice for orders with total = 0 and status pending as well)
    if order.status not in [Order.STATUS_AWAITING_PAYMENT, Order.STATUS_CANCELLED] and not order.invoices.all().exists():
        # create invoice if paid
        order.create_invoice(status=Invoice.STATUS.PAID)

    # notify stuff
    notify_about_new_order.delay(order)


@receiver(pre_save, sender=Order)
@apm_custom_context('signals')
def order_status_changed(sender, instance, **kwargs):
    if instance.pk and SignalsHelper.attribute_changed(instance, ['status']):
        # notify customer
        notify_about_changed_order_status.delay(instance)

        # only if order status == payment received? (NO!, because we need to create invoice for orders with total = 0 and status pending as well)
        if instance.status not in [Order.STATUS_AWAITING_PAYMENT, Order.STATUS_CANCELLED] and not instance.invoices.all().exists():
            # create invoice if paid
            instance.create_invoice(status=Invoice.STATUS.PAID)
