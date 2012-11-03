from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _


class Catalog(models.Model):
    title = models.CharField(_(u'title'), max_length=255)
    description = models.TextField(
        _(u'description'), blank=True, default=None, null=True)
    slug = models.SlugField(_(u'slug'), max_length=255)
    weight = models.SmallIntegerField(_(u'weight'), default=0)
    created = models.DateTimeField(_(u'created'), default=now())
    modified = models.DateTimeField(_(u'modified'))

    class Meta:
        app_label = 'commerce'
        db_table = 'commerce_catalogs'
        verbose_name = _(u'catalog')
        verbose_name_plural = _(u'catalogs')
        ordering = ('title', '-weight')

    def __unicode__(self):
        return self.title

    def save(self, **kwargs):
        self.modified = now()
        super(Catalog, self).save(**kwargs)

    @models.permalink
    def get_absolute_url(self):
        return 'commerce_catalogs_detail', [self.slug, ]

    def count_products(self):
        return self.product_set.all().count()

    def get_products(self):
        return self.product_set.all().visible()
