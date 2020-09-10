from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils.timezone import now



class CartQuerySet(models.QuerySet):
    def old(self, days=1):
        threshold = now() - timedelta(days=days)
        return self.filter(created__lte=threshold)


class OrderQuerySet(models.QuerySet):
    def awaiting_payment(self):
        return self.filter(status=self.model.STATUS_AWAITING_PAYMENT)

    def paid_not_cancelled_nor_refunded(self):
        return self.exclude(status__in=[
            self.model.STATUS_AWAITING_PAYMENT,
            self.model.STATUS_CANCELLED,
            self.model.STATUS_REFUNDED,
            self.model.STATUS_PARTIALLY_REFUNDED,
        ])

    def not_cancelled_nor_refunded(self):
        return self.exclude(status__in=[
            self.model.STATUS_CANCELLED,
            self.model.STATUS_REFUNDED,
            self.model.STATUS_PARTIALLY_REFUNDED,
        ])

    def not_cancelled(self):
        return self.exclude(status__in=[
            self.model.STATUS_CANCELLED,
        ])

    def not_reminded(self):
        return self.filter(reminder_sent=None)

    def old(self, days=7):
        threshold = now() - timedelta(days=days)
        return self.filter(created__lte=threshold)

    # TODO: move to some kind of mixin (ideally into django-pragmatic)
    def lock(self):
        """ Lock table.

        Locks the object model table so that atomic update is possible.
        Simultaneous database access request pend until the lock is unlock()'ed.

        Note: If you need to lock multiple tables, you need to do lock them
        all in one SQL clause and this function is not enough. To avoid
        dead lock, all tables must be locked in the same order.

        If no lock mode is specified, then ACCESS EXCLUSIVE, the most restrictive mode, is used.
        Read more: https://www.postgresql.org/docs/9.4/static/sql-lock.html
        """
        from django.db import connection
        cursor = connection.cursor()
        table = self.model._meta.db_table
        cursor.execute("LOCK TABLE %s" % table)


class PurchasedItemQuerySet(models.QuerySet):
    def of_not_cancelled_nor_refunded_orders(self):
        from commerce.models import Order
        return self.exclude(order__status__in=[
            Order.STATUS_CANCELLED,
            Order.STATUS_REFUNDED,
            Order.STATUS_PARTIALLY_REFUNDED,
        ])


class DiscountCodeQuerySet(models.QuerySet):
    def valid(self):
        return self.filter(Q(valid_until=None) | Q(valid_until__gte=now()))

    def infinite(self):
        return self.filter(usage=self.model.USAGE_INFINITE)

    def promoted(self):
        return self.filter(promoted=True)

    def add_to_cart(self):
        return self.filter(add_to_cart=True)

    def for_content_types(self, content_types):
        return self.filter(content_types__in=content_types)


class ShippingOptionQuerySet(models.QuerySet):
    def for_country(self, country):
        country_shipping_options = self.filter(countries__contains=[country])

        if country_shipping_options.exists():
            # country specific shipping options
            return country_shipping_options

        # shipping options for all countries (general)
        return self.filter(countries=[])
