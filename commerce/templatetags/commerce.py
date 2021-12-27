from decimal import Decimal

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import EMPTY_VALUES

from commerce.context_processors import discount_codes
from commerce.models import Discount, AbstractProduct

register = template.Library()


@register.simple_tag(takes_context=True)
def discount_for_product(context, product):
    valid_product_discounts = Discount.objects.for_product(product).valid()

    # promoted discount
    valid_promoted_infinite_codes = discount_codes(context['request'])['valid_promoted_discount_codes'].for_product(product)
    discount = valid_promoted_infinite_codes.first()

    try:
        # cart discount
        user = context['request'].user

        if user.cart.discount:
            discount = user.cart.discount
    except (ObjectDoesNotExist, AttributeError):
        pass

    if discount:
        discount = valid_product_discounts.filter(id=discount.id).first()
        return discount

    return None


@register.filter()
def percentage_discount_price(price, amount):
    if price in EMPTY_VALUES or price == 0:
        return 0

    percentage = Decimal(100-amount)/100
    discount_price = round(price * percentage, 2)
    discount_price = str(discount_price)

    if discount_price.endswith('.00'):
        discount_price = discount_price[:-3]

    return discount_price


@register.filter()
def in_stock(product, option):
    return option.in_stock(product)
