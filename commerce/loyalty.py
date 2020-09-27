from decimal import Decimal
from commerce import settings as commerce_settings


def unused_points(user):
    points = 0

    # earned points
    for order in user.order_set.not_cancelled():
        points += order.loyalty_points_earned

    # used points
    if user.cart:
        points -= user.cart.loyalty_points_used

    return points


def points_to_currency_unit(points):
    return round(Decimal(points * commerce_settings.CURRENCY_UNITS_PER_LOYALTY_POINT), 2)
