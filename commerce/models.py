from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from commerce import settings as commerce_settings


class AbstractProduct(models.Model):
    in_stock = models.SmallIntegerField(_('in stock'), help_text=_('empty value means infinite availability'), validators=[MinValueValidator(0)], blank=True, null=True, default=None)
    price = models.DecimalField(_('price'), help_text=commerce_settings.CURRENCY, max_digits=10, decimal_places=2, db_index=True, validators=[MinValueValidator(0)],
                                blank=True, null=True, default=None)
    # discount = models.DecimalField(_(u'discount (%)'), max_digits=4, decimal_places=1, default=0)
    awaiting = models.BooleanField(_('awaiting'), default=False)

    class Meta:
        abstract = True
