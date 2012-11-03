# -*- coding: utf-8

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

COMMERCE_URL = getattr(settings, 'COMMERCE_URL', 'http://www.example.com')
COMMERCE_PRODUCTS_PER_PAGE = getattr(settings, 'COMMERCE_PRODUCTS_PER_PAGE', 9)
COMMERCE_CURRENCY = getattr(settings, 'COMMERCE_CURRENCY', '€')
COMMERCE_TAX = getattr(settings, 'COMMERCE_TAX', 20)
COMMERCE_EMAIL_FROM = getattr(settings, 'COMMERCE_EMAIL_FROM', 'info@fitt.sk')

# Images
COMMERCE_THUMBNAIL_SIZE = getattr(
    settings, 'COMMERCE_THUMBNAIL_SIZE', '210x210')

# Countries
COUNTRIES = (
    ('SR', _(u'Slovak republic')),
    ('CR', _(u'Czech republic')))

COMMERCE_COUNTRIES = getattr(settings, 'COMMERCE_COUNTRIES', COUNTRIES)

# Shippings
COMMERCE_SHIPPING_SLOVAK_POST = 'SLOVAK_POST'
SHIPPINGS = (
    (COMMERCE_SHIPPING_SLOVAK_POST, _(u'Slovak Post')),
)
COMMERCE_SHIPPINGS = getattr(settings, 'COMMERCE_SHIPPINGS', SHIPPINGS)
COMMERCE_SHIPPINGS_PAYMENTS = getattr(
    settings, 'COMMERCE_SHIPPINGS_PAYMENTS', list())

# Payments
COMMERCE_PAYMENT_DELIVERY = 'DELIVERY'
PAYMENTS = (
    (COMMERCE_PAYMENT_DELIVERY, _(u'Delivery')),
)
COMMERCE_PAYMENTS = getattr(settings, 'COMMERCE_PAYMENTS', PAYMENTS)

# States
COMMERCE_STATE_NEW = 'NEW'
COMMERCE_STATE_VERIFIED = 'VERIFIED'
COMMERCE_STATE_PROCESS = 'PROCESS'
COMMERCE_STATE_SHIPPED = 'SHIPPED'
COMMERCE_STATE_CLOSED = 'CLOSED'

STATES = (
    (COMMERCE_STATE_NEW, _(u'New order')),
    (COMMERCE_STATE_VERIFIED, _(u'Verified')),
    (COMMERCE_STATE_PROCESS, _(u'In process')),
    (COMMERCE_STATE_SHIPPED, _(u'Shipped')),
    (COMMERCE_STATE_CLOSED, _(u'Closed'))
)
COMMERCE_STATES = getattr(settings, 'COMMERCE_STATES', STATES)
