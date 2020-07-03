from django.db.models.signals import pre_save
from django.dispatch import receiver

from commerce.models import Order
from commerce.tasks import notify_about_changed_order_status
from pragmatic.signals import apm_custom_context, SignalsHelper


@receiver(pre_save, sender=Order)
@apm_custom_context('signals')
def order_status_changed(sender, instance, **kwargs):
    if instance.pk and SignalsHelper.attribute_changed(instance, ['status']):
        notify_about_changed_order_status(instance)
