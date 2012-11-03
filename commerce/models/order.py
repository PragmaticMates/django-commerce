from __future__ import division

from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from commerce.app_settings import COMMERCE_PAYMENTS, COMMERCE_SHIPPINGS, \
    COMMERCE_SHIPPING_SLOVAK_POST, COMMERCE_PAYMENT_DELIVERY, \
    COMMERCE_COUNTRIES, COMMERCE_STATES, COMMERCE_STATE_NEW, COMMERCE_TAX
from commerce.models.product import Product
from commerce.managers.order import OrderManager


class Order(models.Model):
    user = models.ForeignKey(User, 'id', verbose_name=_(u'user'))
    total = models.FloatField(_(u'total'))
    state = models.CharField(
        _(u'state'),
        max_length=70, choices=COMMERCE_STATES, default=COMMERCE_STATE_NEW)
    shipping = models.CharField(
        _(u'shipping'),
        choices=COMMERCE_SHIPPINGS, max_length=70)
    price_shipping = models.FloatField(_(u'price shipping'))
    payment = models.CharField(
        _(u'payment'),
        choices=COMMERCE_PAYMENTS, max_length=70)
    created = models.DateTimeField(_(u'created'), default=now())
    modified = models.DateTimeField(_(u'modified'))
    objects = OrderManager()

    class Meta:
        app_label = 'commerce'
        db_table = 'commerce_orders'
        verbose_name = _(u'order')
        verbose_name_plural = _(u'orders')
        ordering = ('-pk', )

    def __unicode__(self):
        return self.identifier()

    def save(self, **kwargs):
        self.modified = now()
        super(Order, self).save(**kwargs)

    def identifier(self):
        return '#%(ident)s' % {
            'ident': str(self.pk).rjust(4, '0')
        }

    def subtotal(self):
        return self.total / ((COMMERCE_TAX + 100) / 100)

    def tax(self):
        return self.total * (COMMERCE_TAX / 100)

    def get_information(self):
        return self.information_set.all()[0]


class Line(models.Model):
    order = models.ForeignKey(Order, 'id', verbose_name=_(u'order'))
    product = models.ForeignKey(Product, 'id', verbose_name=_(u'product'))
    quantity = models.SmallIntegerField(_(u'quantity'))
    total = models.FloatField(_(u'total'))
    price = models.FloatField(_(u'price'))
    price_discount = models.FloatField(
        _(u'price discount'), default=None, null=True, blank=True)
    created = models.DateTimeField(_(u'created'), default=now())
    modified = models.DateTimeField(_(u'modified'))

    class Meta:
        app_label = 'commerce'
        db_table = 'commerce_lines'
        verbose_name = _('line')
        verbose_name_plural = _(u'lines')
        ordering = ('-created', )

    def save(self, **kwargs):
        self.modified = now()
        return super(Line, self).save(**kwargs)


class Information(models.Model):
    order = models.ForeignKey(Order, 'id', verbose_name=_(u'order'))

    company_name = models.CharField(
        _(u'company name'),
        max_length=255, default=None, blank=True, null=True)
    company_tax_id = models.CharField(
        _(u'TAX ID'), max_length=255, default=None, blank=True, null=True)
    company_id = models.CharField(
        _(u'ID'), max_length=255, default=None, blank=True, null=True)
    company_vat = models.CharField(
        _(u'VAT'), max_length=255, default=None, blank=True, null=True)

    street_and_number = models.CharField(
        _(u'street and number'), max_length=255)
    city = models.CharField(_(u'city'), max_length=255)
    zip = models.CharField(_(u'ZIP'), max_length=255)
    country = models.CharField(
        _(u'country'), max_length=255, choices=COMMERCE_COUNTRIES)
    phone = models.CharField(
        _(u'phone'), max_length=255, default=None, blank=True, null=True)

    shipping_company_name = models.CharField(
        _(u'company name'),
        max_length=255, default=None, blank=True, null=True)
    shipping_first_name = models.CharField(
        _(u'first name'), max_length=255)
    shipping_last_name = models.CharField(
        _(u'last name'), max_length=255)
    shipping_street_and_number = models.CharField(
        _(u'street and number'), max_length=255)
    shipping_city = models.CharField(_(u'city'), max_length=255)
    shipping_zip = models.CharField(_(u'ZIP'), max_length=255)
    shipping_country = models.CharField(
        _(u'country'), max_length=255, choices=COMMERCE_COUNTRIES)

    created = models.DateTimeField(_(u'created'), default=now())
    modified = models.DateTimeField(_(u'modified'), )

    class Meta:
        app_label = 'commerce'
        db_table = 'commerce_information'
        verbose_name = _(u'information')
        verbose_name_plural = _(u'information')
        ordering = ('-created', )

    def save(self, **kwargs):
        self.modified = now()
        super(Information, self).save(**kwargs)


import commerce.signals
