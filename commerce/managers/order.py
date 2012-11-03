from django.db import models


class OrderQuerySet(models.query.QuerySet):
    def by_user(self, user):
        return self.filter(user=user)


class OrderManager(models.Manager):
    def get_query_set(self):
        return OrderQuerySet(self.model, using=self._db)

    def by_user(self, user):
        return self.get_query_set(user)
