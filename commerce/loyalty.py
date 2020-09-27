from decimal import Decimal
from commerce import settings as commerce_settings


def earned_points(user):
    return sum([order.loyalty_points_earned for order in user.order_set.with_earned_loyalty_points()])


def available_points(cart):
    items_subtotal = cart.items_subtotal
    user_earned_points = earned_points(cart.user)
    user_earned_points_in_currency_unit = points_to_currency_unit(user_earned_points)

    if user_earned_points_in_currency_unit > items_subtotal:
        return int(items_subtotal / commerce_settings.CURRENCY_UNITS_PER_LOYALTY_POINT)

    return user_earned_points


def unused_points(user):
    # earned points
    points = earned_points(user)

    # used points
    if user.cart:
        points -= user.cart.loyalty_points_used

    return points


def points_to_currency_unit(points):
    return round(Decimal(points * commerce_settings.CURRENCY_UNITS_PER_LOYALTY_POINT), 2)


def currency_units_to_points(value):
    return int(value * commerce_settings.LOYALTY_POINTS_PER_CURRENCY_UNIT)
