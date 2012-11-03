from django.db import models
from django.db.models import Q


class ProductQuerySet(models.query.QuerySet):
    def visible(self):
        return self.filter(
            not_visible_individually=False
        ).prefetch_related('manufacturer')

    def search(self, q):
        return self.filter(Q(title__icontains=q) | Q(description__icontains=q))


class ProductManager(models.Manager):
    def get_query_set(self):
        return ProductQuerySet(self.model, using=self._db)

    def visible(self):
        return self.get_query_set().visible()

    def search(self, q):
        return self.get_query_set().search(q)
