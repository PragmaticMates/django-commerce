from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from commerce.models.catalog import Catalog


class CatalogAdmin(admin.ModelAdmin):
    fields = ('title', 'slug', 'description')
    list_display = ('title', 'url', 'count_products')

    def count_products(self, obj):
        return obj.count_products()
    count_products.short_description = _(u'Of products')

    def url(self, obj):
        return '<a href="%s">%s</a>' % (obj.get_absolute_url(), obj.slug)
    url.allow_tags = True


admin.site.register(Catalog, CatalogAdmin)
