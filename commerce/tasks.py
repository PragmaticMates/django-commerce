from django.contrib.auth import get_user_model
from django.utils.translation import override as override_language, ugettext_lazy as _

from commerce.managers import EmailManager
from pragmatic.signals import apm_custom_context


@apm_custom_context('tasks')
def notify_about_changed_order_status(order):
    user = order.user

    with override_language(user.preferred_language):
        return EmailManager.send_mail(user, 'ORDER_STATUS_CHANGED', _('Status of order %d changed') % order.number, data={'order': order}, request=None)


@apm_custom_context('tasks')
def notify_about_new_file(file):
    for user in get_user_model().objects.active().superusers():
        with override_language(user.preferred_language):
            return EmailManager.send_mail(user, 'FILE_UPLOADED', _('New file uploaded'), data={'file': file}, request=None)


@apm_custom_context('tasks')
def notify_about_changed_file_folder(file):
    owner = file.owner
    folder = file.folder

    if owner:
        with override_language(owner.preferred_language):
            # TODO: configurable subject
            subject = _('File approved') if folder else _('File rejected')
            return EmailManager.send_mail(owner, 'FILE_FOLDER_CHANGED', subject, data={'file': file}, request=None)


@apm_custom_context('tasks')
def notify_about_deleted_file(file):
    owner = file.owner

    if owner:
        with override_language(owner.preferred_language):
            return EmailManager.send_mail(owner, 'FILE_DELETED', _('File deleted'), data={'file': file}, request=None)
