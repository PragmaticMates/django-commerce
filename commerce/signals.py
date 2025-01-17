import django.dispatch
from django.db.models.signals import pre_save
from django.dispatch import receiver
from invoicing.models import Invoice

from commerce import settings as commerce_settings
from commerce.models import Order, Cart
from commerce.tasks import notify_about_new_order, notify_about_changed_order_status
from pragmatic.signals import apm_custom_context, SignalsHelper

checkout_finished = django.dispatch.Signal()
cart_updated = django.dispatch.Signal()
invoice_created = django.dispatch.Signal()


@receiver(checkout_finished, sender=Cart)
@apm_custom_context('signals')
def order_created(sender, order, **kwargs):
    if not order.invoices.all().exists():
        if order.status == Order.STATUS_AWAITING_PAYMENT and commerce_settings.CREATE_PROFORMA_INVOICE:
            # create proforma invoice
            order.create_invoice(type=Invoice.TYPE.PROFORMA, status=Invoice.STATUS.NEW, creator=order.user)

        # only if order status == payment received? (NO!, because we need to create invoice for orders with total = 0 and status pending as well)
        elif order.status not in [Order.STATUS_AWAITING_PAYMENT, Order.STATUS_CANCELLED]:
            # create invoice if paid
            order.create_invoice(type=Invoice.TYPE.INVOICE, status=Invoice.STATUS.PAID, creator=order.user)

    # notify stuff and customer
    notify_about_new_order.delay(order)


@receiver(pre_save, sender=Order)
@apm_custom_context('signals')
def order_status_changed(sender, instance, **kwargs):
    if instance.pk and SignalsHelper.attribute_changed(instance, ['status']):
        # only if order status == payment received? (NO!, because we need to create invoice for orders with total = 0 and status pending as well)
        if instance.status not in [Order.STATUS_AWAITING_PAYMENT, Order.STATUS_CANCELLED] and not instance.invoices.all().exists():
            # create invoice if paid
            instance.create_invoice(type=Invoice.TYPE.INVOICE, status=Invoice.STATUS.PAID, creator=instance.user)

        # notify customer
        if instance.status in commerce_settings.NOTIFY_ABOUT_STATUSES:
            notify_about_changed_order_status.delay(instance)
