from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now


class Manufacturer(models.Model):
    title = models.CharField(_(u'title'), max_length=255)
    created = models.DateTimeField(_(u'created'), default=now())
    modified = models.DateTimeField(_(u'modified'))

    class Meta:
        app_label = 'commerce'
        db_table = 'commerce_manufacturers'
        verbose_name = _(u'manufacturer')
        verbose_name_plural = _(u'manufacturers')
        ordering = ('title', )

    def __unicode__(self):
        return self.title

    def save(self, **kwargs):
        self.modified = now()
        super(Manufacturer, self).save(**kwargs)
