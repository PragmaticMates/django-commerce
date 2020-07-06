from decimal import Decimal

from django import template
from django.contrib.contenttypes.models import ContentType
from django.core.validators import EMPTY_VALUES

from commerce.models import Discount

register = template.Library()


@register.simple_tag()
def discount_for_product(product):
    ct = ContentType.objects.get_for_model(product.__class__)
    discounts = Discount.objects.valid().order_by('valid_until').for_content_types([ct])
    discount = discounts.first()
    return discount


@register.filter()
def discount_price(price, amount):
    if price in EMPTY_VALUES or price == 0:
        return 0

    print(price, amount)

    percentage = Decimal(100-amount)/100
    print(percentage)
    discount_price = round(price * percentage, 2)
    print(discount_price)
    discount_price = str(discount_price)

    if discount_price.endswith('.00'):
        discount_price = discount_price[:-3]

    return discount_price
