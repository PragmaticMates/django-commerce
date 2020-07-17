import django.dispatch
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from filer.models import File, Image

from commerce.models import Order, Cart
from commerce.tasks import notify_about_new_order, notify_about_changed_order_status, notify_about_new_file, notify_about_changed_file_folder, notify_about_deleted_file
from pragmatic.signals import apm_custom_context, SignalsHelper

checkout_finished = django.dispatch.Signal(providing_args=["order"])


@receiver(checkout_finished, sender=Cart)
@apm_custom_context('signals')
def order_created(sender, order, **kwargs):
    # create invoice if paid
    if order.status not in [Order.STATUS_AWAITING_PAYMENT, Order.STATUS_CANCELLED]:
        order.create_invoice()

    # notify stuff
    notify_about_new_order(order)


@receiver(pre_save, sender=Order)
@apm_custom_context('signals')
def order_status_changed(sender, instance, **kwargs):
    if instance.pk and SignalsHelper.attribute_changed(instance, ['status']):
        # notify customer
        notify_about_changed_order_status(instance)

        # create invoice if paid
        if instance.status not in [Order.STATUS_AWAITING_PAYMENT, Order.STATUS_CANCELLED]:
            instance.create_invoice()


@receiver(post_save, sender=File)
@receiver(post_save, sender=Image)
@apm_custom_context('signals')
def file_created(sender, instance, created, **kwargs):
    if created:
        notify_about_new_file(instance)


@receiver(pre_save, sender=File)
@receiver(pre_save, sender=Image)
@apm_custom_context('signals')
def file_folder_changed(sender, instance, **kwargs):
    if instance.pk and SignalsHelper.attribute_changed(instance, ['folder']):
        notify_about_changed_file_folder(instance)


@receiver(post_delete, sender=File)
@apm_custom_context('signals')
def file_deleted(sender, instance, **kwargs):
    notify_about_deleted_file(instance)
