from django.db import models
from django.utils.translation import ugettext_lazy as _


class Order(models.Model):
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_PAID = 'PAID'
    STATUS_PARTIAL = 'PARTIAL'
    STATUS_CANCELED = 'CANCELED'
    STATUS_UNPAID = 'UNPAID'
    STATUS_RETURNED = 'RETURNED'

    STATUSES = [
        (STATUS_PROCESSING, _('processing')),
        (STATUS_APPROVED, _('approved')),
        (STATUS_PAID, _('paid')),
        (STATUS_PARTIAL, _('partial')),
        (STATUS_CANCELED, _('canceled')),
        (STATUS_UNPAID, _('unpaid')),
        (STATUS_RETURNED, _('returned')),
    ]
    order = models.ForeignKey('commerce.Order', verbose_name=_('order'), on_delete=models.CASCADE)
    status = models.CharField(_('status'), choices=STATUSES, max_length=10, default=STATUS_PROCESSING, db_index=True)
    created = models.DateTimeField(_('created'), auto_now_add=True, db_index=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('order')
        ordering = ('created',)
        get_latest_by = 'created'

    def __str__(self):
        return str(self.id)
