from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from commerce import settings as commerce_settings


class AbstractProduct(models.Model):
    in_stock = models.SmallIntegerField(_('in stock'), help_text=_('empty value means infinite availability'), validators=[MinValueValidator(0)], blank=True, null=True, default=None)
    price = models.DecimalField(_('price'), help_text=commerce_settings.CURRENCY, max_digits=10, decimal_places=2, db_index=True, validators=[MinValueValidator(0)],
                                blank=True, null=True, default=None)
    # discount = models.DecimalField(_(u'discount (%)'), max_digits=4, decimal_places=1, default=0)
    awaiting = models.BooleanField(_('awaiting'), default=False)

    # WARNING! don't use generic relation in parent classes. Add them into child classes instead
    # cart_items = GenericRelation('commerce.Item', related_query_name='product')

    class Meta:
        abstract = True


class Cart(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    created = models.DateTimeField(_('created'), auto_now_add=True, db_index=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    # delivery details
    # contact details
    # billing details
    # shipping details
    # discount

    class Meta:
        verbose_name = _('shopping cart')
        verbose_name_plural = _('shopping carts')

    def __str__(self):
        return str(self.user)
    
    @property
    def total(self):
        total = 0

        for item in self.item_set.all():
            total += item.subtotal

        # TODO: + shipping
        # TODO - discount
        return total

    @property
    def open(self):
        return now() - self.created


class Item(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey('content_type', 'object_id')
    quantity = models.PositiveSmallIntegerField(verbose_name=_('quantity'))
    created = models.DateTimeField(_('created'), auto_now_add=True, db_index=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    class Meta:
        verbose_name = _('item')
        verbose_name_plural = _('items')

    def __str__(self):
        return str(self.product)

    @property
    def subtotal(self):
        return self.quantity * self.product.price
