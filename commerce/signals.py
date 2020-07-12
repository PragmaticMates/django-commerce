from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from filer.models import File, Image

from commerce.models import Order
from commerce.tasks import notify_about_new_order, notify_about_changed_order_status, notify_about_new_file, notify_about_changed_file_folder, notify_about_deleted_file
from pragmatic.signals import apm_custom_context, SignalsHelper


@receiver(post_save, sender=Order)
@apm_custom_context('signals')
def order_created(sender, instance, created, **kwargs):
    if created:
        # TODO: schedule in few seconds (to save m2m related objects)
        notify_about_new_order(instance)


@receiver(pre_save, sender=Order)
@apm_custom_context('signals')
def order_status_changed(sender, instance, **kwargs):
    if instance.pk and SignalsHelper.attribute_changed(instance, ['status']):
        notify_about_changed_order_status(instance)


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
