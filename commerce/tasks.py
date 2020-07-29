from django.contrib.auth import get_user_model
from django.utils.translation import override as override_language, ugettext_lazy as _
from django_rq import job

from pragmatic.managers import EmailManager
from pragmatic.signals import apm_custom_context

from commerce import settings as commerce_settings


@job(commerce_settings.REDIS_QUEUE)
@apm_custom_context('tasks')
def notify_about_new_order(order):
    for user in get_user_model().objects.active().with_perm('commerce.view_order'):
        with override_language(user.preferred_language):
            EmailManager.send_mail(user, 'commerce/mails/order_created', _('New order'), data={'order': order}, request=None)

    order.send_details()


@job(commerce_settings.REDIS_QUEUE)
@apm_custom_context('tasks')
def notify_about_changed_order_status(order):
    user = order.user

    with override_language(user.preferred_language):
        return EmailManager.send_mail(user, 'commerce/mails/order_status_changed', _('Status of order %d changed') % order.number, data={'order': order}, request=None)
