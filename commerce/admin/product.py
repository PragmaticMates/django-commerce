from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from commerce.models.product import Product


class ProductInline(admin.StackedInline):
    model = Product
    fields = ('title', 'price', 'is_price_with_tax', 'price_discount',
              'price_common')
    extra = 0


class ProductAdmin(admin.ModelAdmin):
    fields = ('title', 'catalog', 'slug', 'description',
              'cover', 'price', 'price_discount', 'price_common',
              'is_price_with_tax', 'is_new', 'is_top',
              'on_stock')
    list_display = ('title', 'price',  'price_discount')
    list_editable = ('price', 'price_discount')
    list_filter = ('is_price_with_tax', 'catalog', )
    list_per_page = 20

    def get_object(self, request, object_id):
        object = super(ProductAdmin, self).get_object(request, object_id)
        if object.pk is not None:
            self.inlines = (ProductInline,)
        return object

    def queryset(self, request):
        qs = super(ProductAdmin, self).queryset(request)
        return qs.filter(not_visible_individually=False)

    def get_price(self, obj):
        return obj.get_price()
    get_price.short_description = _(u'Price')

    def get_associated_products_count(self, obj):
        return obj.get_associated_products().count()

    get_associated_products_count.short_description = _(u'Associated products')


admin.site.register(Product, ProductAdmin)
