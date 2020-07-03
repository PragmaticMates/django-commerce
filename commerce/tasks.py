from django.utils.translation import override as override_language, ugettext_lazy as _

from commerce.managers import EmailManager
from pragmatic.signals import apm_custom_context


@apm_custom_context('tasks')
def notify_about_changed_order_status(instance):
    user = instance.user

    with override_language(user.preferred_language):
        return EmailManager.send_mail(user, 'ORDER_STATUS_CHANGED', _('Status of order %d changed') % instance.number, data={'order': instance}, request=None)
