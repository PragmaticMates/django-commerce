from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Customer(models.Model):
    user = models.OneToOneField(get_user_model(), verbose_name=_('user'), on_delete=models.CASCADE)
    stripe_id = models.CharField(_('Stripe ID'), max_length=255, db_index=True)
    payment_method = models.CharField(_('Payment method ID'), max_length=255, db_index=True, blank=True)
    created = models.DateTimeField(_('created'), auto_now_add=True, db_index=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    class Meta:
        verbose_name = _('customer')
        verbose_name_plural = _('customers')
        ordering = ('created',)
        get_latest_by = 'created'

    def __str__(self):
        return str(self.user)
