from django.db import models
from django.utils.translation import ugettext_lazy as _
from commerce import settings as commerce_settings


class Payment(models.Model):
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
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ('created',)
        get_latest_by = 'created'

    def __str__(self):
        return str(self.id)


class Result(models.Model):
    payment = models.ForeignKey(Payment, verbose_name=_('order'), on_delete=models.CASCADE)
    operation = models.CharField(_('operation'), max_length=20)
    ordernumber = models.PositiveIntegerField(_('order number'))
    merordernum = models.PositiveIntegerField(_('merchant order number'), blank=True, null=True, default=None)
    md = models.CharField(_('md'), max_length=255, blank=True, null=True, default=None)
    prcode = models.PositiveIntegerField(_('primary code'))
    srcode = models.PositiveIntegerField(_('secondary code'))
    resulttext = models.CharField(_('result text'), max_length=255, blank=True, null=True, default=None)
    userparam1 = models.CharField(_('user param 1'), max_length=64, blank=True, null=True, default=None)
    addinfo = models.CharField(_('additional information'), max_length=255, blank=True, null=True, default=None)
    token = models.CharField(_('token'), max_length=64, blank=True, null=True, default=None)
    expiry = models.CharField(_('expiration'), max_length=4, blank=True, null=True, default=None)
    acsres = models.CharField(_('authorisation centre result'), max_length=1, blank=True, null=True, default=None)
    accode = models.CharField(_('authorisation centre code'), max_length=6, blank=True, null=True, default=None)
    panpattern = models.CharField(_('masked card number'), max_length=19, blank=True, null=True, default=None)
    daytocapture = models.CharField(_('day to capture'), max_length=8, blank=True, null=True, default=None)
    tokenregstatus = models.CharField(_('token registration status'), max_length=10, blank=True, null=True, default=None)
    acrc = models.CharField(_('authorisation centre result code'), max_length=2, blank=True, null=True, default=None)
    rrn = models.CharField(_('retrieval reference number'), max_length=12, blank=True, null=True, default=None)
    par = models.CharField(_('payment account reference'), max_length=29, blank=True, null=True, default=None)
    traceid = models.CharField(_('trace ID'), max_length=15, blank=True, null=True, default=None)
    digest = models.TextField(_('digest'))
    digest1 = models.TextField(_('digest 1'))
    created = models.DateTimeField(_('created'), auto_now_add=True, db_index=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    class Meta:
        verbose_name = _('result')
        verbose_name_plural = _('results')
        ordering = ('created',)
        get_latest_by = 'created'

    def __str__(self):
        return str(self.id)

    def is_valid(self):
        payment_manager = self.payment.order.payment_manager

        data_to_verify = f'{self.operation}'
        for attr in ['ordernumber', 'merordernum', 'md', 'prcode', 'srcode', 'resulttext', 'userparam1', 'addinfo', 'token', 'expiry', 'acsres', 'accode', 'panpattern', 'daytocapture', 'tokenregstatus', 'acrc', 'rrn', 'par', 'traceid']:
            value = getattr(self, attr)
            if value is not None:
                data_to_verify += f'|{value}'

        digest_verified = payment_manager.verify(self.digest, data_to_verify)
        digest1_verified = payment_manager.verify(self.digest1, data_to_verify + f'|{commerce_settings.GATEWAY_GP_MERCHANT_NUMBER}')
        return digest_verified and digest1_verified
