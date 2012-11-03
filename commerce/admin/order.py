from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from commerce.models.order import Order, Line, Information
from commerce.templatetags.utils import format_price


class LineInline(admin.StackedInline):
    model = Line
    readonly_fields = ('product', )
    exclude = ('created', 'modified')
    extra = 0


class ShippingInline(admin.StackedInline):
    model = Information
    exclude = ('created', 'modified')
    extra = 0
    max_num = 1
    can_delete = False
    verbose_name = _(u'Shipping address')
    fields = ('shipping_first_name', 'shipping_last_name',
              'shipping_company_name', 'shipping_street_and_number',
              'shipping_city', 'shipping_zip', 'shipping_country')


class InvoicingInline(admin.StackedInline):
    model = Information
    exclude = ('created', 'modified')
    extra = 0
    max_num = 1
    can_delete = False
    verbose_name = _(u'Invoicing infomation')
    fields = ('company_name', 'company_tax_id', 'company_vat', 'company_id',
              'street_and_number', 'city', 'zip', 'country', 'phone')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'lines_count', 'price', 'state')
    list_editable = ('state', )
    list_filter = ('state',)
    list_per_page = 10
    inlines = [InvoicingInline, ShippingInline, LineInline]
    exclude = ('created', 'modified',)

    def lines_count(self, obj):
        return obj.line_set.count()
    lines_count.short_description = _('count lines')

    def price(self, obj):
        return format_price(obj.total)
    price.short_description = _(u'total')


admin.site.register(Order, OrderAdmin)
