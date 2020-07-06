from django.db import models
from django.utils.timezone import now


class OrderQuerySet(models.QuerySet):
    def paid_not_cancelled_nor_refunded(self):
        return self.exclude(status__in=[
            self.model.STATUS_AWAITING_PAYMENT,
            self.model.STATUS_CANCELLED,
            self.model.STATUS_REFUNDED,
            self.model.STATUS_PARTIALLY_REFUNDED,
        ])

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


class DiscountCodeQuerySet(models.QuerySet):
    def valid(self):
        return self.filter(valid_until__gte=now())

    def promoted(self):
        return self.filter(promoted=True)

    def add_to_cart(self):
        return self.filter(add_to_cart=True)

    def for_content_types(self, content_types):
        return self.filter(content_types__in=content_types)
