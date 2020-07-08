from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from modeltrans.admin import ActiveLanguageMixin

from commerce.models import Cart, Item, Shipping, Payment, Order, PurchasedItem, Option, Discount, Supply


if not admin.site.is_registered(ContentType):
    @admin.register(ContentType)
    class ContentTypeAdmin(admin.ModelAdmin):
        search_fields = ['app_label', 'model']


class ItemInline(admin.StackedInline):
    model = Item
    extra = 1


class SupplyInline(GenericStackedInline):
    model = Supply
    extra = 1
    max_num = 1


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'items', 'total', 'delivery_country', 'created', 'modified', 'open')
    list_select_related = ['user']
    inlines = [ItemInline]
    fieldsets = [
        (None, {'fields': ['user']}),
        (_('Delivery address'), {'fields': [('delivery_name', 'delivery_street', 'delivery_postcode', 'delivery_city', 'delivery_country')]}),
        (_('Billing address'), {'fields': [('billing_name', 'billing_street', 'billing_postcode', 'billing_city', 'billing_country')]}),
        (_('Billing details'), {'fields': [('reg_id', 'tax_id', 'vat_id')]}),
        (_('Contact details'), {'fields': [('email', 'phone')]}),
        (_('Shipping'), {'fields': ['shipping_option', 'payment_method']}),
        (_('Others'), {'fields': ['discount', ]}),
        (_('Timestamps'), {'fields': ['created', 'modified']}),
    ]
    readonly_fields = ['created', 'modified']

    def items(self, obj):
        return ', '.join([str(item) for item in obj.item_set.all()])


@admin.register(Option)
class OptionAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    list_display = ('id', 'title_i18n')  # TODO: content types?


@admin.register(Shipping)
class ShippingAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    list_display = ('id', 'title_i18n', 'fee', 'countries')


@admin.register(Payment)
class PaymentAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    list_display = ('id', 'title_i18n', 'fee', 'method', 'shipping_options')

    def shipping_options(self, obj):
        return ', '.join([str(shipping) for shipping in obj.shippings.all()])


class PurchasedItemInline(admin.StackedInline):
    model = PurchasedItem
    extra = 1
    autocomplete_fields = ['files']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    actions = ['create_invoice']
    list_display = ('number', 'status', 'user', 'purchased_items', 'total', 'delivery_country', 'shipping_option', 'payment_method', 'created', 'modified')
    list_editable = ['status']
    list_select_related = ['user', 'shipping_option', 'payment_method']
    list_filter = ['shipping_option', 'payment_method', 'status']
    inlines = [PurchasedItemInline]
    fieldsets = [
        (None, {'fields': ['user', 'status', 'number']}),
        (_('Delivery address'), {'fields': [('delivery_name', 'delivery_street', 'delivery_postcode', 'delivery_city', 'delivery_country')]}),
        (_('Billing address'), {'fields': [('billing_name', 'billing_street', 'billing_postcode', 'billing_city', 'billing_country')]}),
        (_('Billing details'), {'fields': [('reg_id', 'tax_id', 'vat_id')]}),
        (_('Contact details'), {'fields': [('email', 'phone')]}),
        (_('Shipping'), {'fields': ['shipping_option', 'shipping_fee', 'payment_method', 'payment_fee']}),
        (_('Billing'), {'fields': ['invoices']}),
        (_('Timestamps'), {'fields': ['created', 'modified']}),
    ]
    autocomplete_fields = ['invoices']
    readonly_fields = ['created', 'modified']

    def purchased_items(self, obj):
        return ', '.join([str(item) for item in obj.purchaseditem_set.all()])

    def create_invoice(self, request, queryset):
        for obj in queryset:
            obj.create_invoice()
    create_invoice.short_description = _('Create invoice')


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'usage', 'description', 'amount', 'valid_until', 'promoted', 'add_to_cart', 'product_types')
    list_filter = ['usage', 'promoted', 'add_to_cart']
    # autocomplete_fields = ['content_types']

    def product_types(self, obj):
        return ', '.join([str(type) for type in obj.content_types.all()])


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    date_hierarchy = 'datetime'
    list_display = ('datetime', 'real_product', 'quantity')
    autocomplete_fields = ['content_type']
