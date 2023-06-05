from django.utils.translation import override as override_language
from django_rq import job
from invoicing.models import Invoice
from invoicing.utils import get_invoices_in_pdf

from pragmatic.managers import EmailManager
from pragmatic.signals import apm_custom_context

from commerce import settings as commerce_settings
from commerce.models import Order

try:
    # older Django
    from django.utils.translation import ugettext_lazy as _
except ImportError:
    # Django >= 3
    from django.utils.translation import gettext_lazy as _


@job(commerce_settings.REDIS_QUEUE)
@apm_custom_context('tasks')
def notify_about_new_order(order):
    # notify staff
    order.notify_staff()

    # notify customer
    order.send_details()


@job(commerce_settings.REDIS_QUEUE)
@apm_custom_context('tasks')
def notify_about_changed_order_status(order):
    user = order.user

    with override_language(user.preferred_language):
        # if payment received: add regular invoice as attachment
        attachments = []

        if order.status in [Order.STATUS_PAYMENT_RECEIVED, Order.STATUS_COMPLETED]:
            invoices = order.invoices.filter(type=Invoice.TYPE.INVOICE)
            export_files = get_invoices_in_pdf(invoices)

            for export_file in export_files:
                attachments.append({
                    'filename': export_file['name'],
                    'content': export_file['content'],
                    'content_type': 'application/pdf'
                })

        return EmailManager.send_mail(
            to=user,
            template_prefix='commerce/mails/order_status_changed',
            subject=_('Status of order %d changed') % order.number,
            data={'order': order},
            attachments=attachments,
            request=None
        )
