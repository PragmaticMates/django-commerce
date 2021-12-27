from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.timezone import now
from gm2m.models import create_gm2m_intermediary_model


class CartQuerySet(models.QuerySet):
    def old(self, days=1):
        threshold = now() - timedelta(days=days)
        return self.filter(created__lte=threshold)

    def empty(self):
        return self.filter(item__isnull=True)


class OrderQuerySet(models.QuerySet):
    def awaiting_payment(self):
        return self.filter(status=self.model.STATUS_AWAITING_PAYMENT)

    def with_earned_loyalty_points(self):
        return self.paid_not_cancelled_nor_refunded()

    def with_spent_loyalty_points(self):
        return self.not_cancelled_nor_refunded()

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

    def old(self, days=7, interval='open'):
        threshold = now() - timedelta(days=days)

        if interval == 'open':
            return self.filter(created__lte=threshold)

        if interval == 'exact':
            return self.filter(
                created__date=threshold.date(),
            )

        raise NotImplementedError(interval)

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

    def of_content_types(self, content_types):
        return self.filter(content_type__in=content_types)


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

    def for_product(self, product):
        ct = ContentType.objects.get_for_model(product.__class__)

        try:
            product_discounts = product.discounts.all()
        except AttributeError:
            product_discounts = self.none()

        field = getattr(self.model, 'products').field
        im = create_gm2m_intermediary_model(field, self.model)
        ids_of_discounts_with_products = set(im.objects.values_list('gm2m_src_id', flat=True))

        # Q(unit=self.model.UNIT_PERCENTAGE),
        return self.filter(
            Q(id__in=product_discounts) |  # specific product discounts
            Q(
                ~Q(id__in=ids_of_discounts_with_products),  # exclude discounts of specific products
                Q(
                    Q(content_types__in=[ct]) |  # content type discounts
                    Q(content_types=None)        # or general discounts
                )
            )
        )


class ShippingOptionQuerySet(models.QuerySet):
    def for_country(self, country):
        country_shipping_options = self.filter(countries__contains=[country])

        if country_shipping_options.exists():
            # country specific shipping options
            return country_shipping_options

        # shipping options for all countries (general)
        return self.filter(countries=[])

    def free(self):
        return self.filter(fee=0)

    def not_free(self):
        return self.exclude(fee=0)
