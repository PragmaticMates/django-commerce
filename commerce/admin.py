from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from commerce.models import Cart, Item, Shipping, Payment, Order, PurchasedItem


class ItemInline(admin.StackedInline):
    model = Item
    extra = 1


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
        (_('Timestamps'), {'fields': ['created', 'modified']}),
    ]
    readonly_fields = ['created', 'modified']

    def items(self, obj):
        return ', '.join([str(item) for item in obj.item_set.all()])


@admin.register(Shipping)
class ShippingAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'fee', 'countries')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'fee', 'method', 'shipping_options')

    def shipping_options(self, obj):
        return ', '.join([str(shipping) for shipping in obj.shippings.all()])


class PurchasedItemInline(admin.StackedInline):
    model = PurchasedItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('number', 'user', 'purchased_items', 'total', 'delivery_country', 'created', 'modified')
    list_select_related = ['user']
    inlines = [PurchasedItemInline]
    fieldsets = [
        (None, {'fields': ['user', 'status', 'number']}),
        (_('Delivery address'), {'fields': [('delivery_name', 'delivery_street', 'delivery_postcode', 'delivery_city', 'delivery_country')]}),
        (_('Billing address'), {'fields': [('billing_name', 'billing_street', 'billing_postcode', 'billing_city', 'billing_country')]}),
        (_('Billing details'), {'fields': [('reg_id', 'tax_id', 'vat_id')]}),
        (_('Contact details'), {'fields': [('email', 'phone')]}),
        (_('Shipping'), {'fields': ['shipping_option', 'shipping_fee', 'payment_method', 'payment_fee']}),
        (_('Timestamps'), {'fields': ['created', 'modified']}),
    ]
    readonly_fields = ['created', 'modified']

    def purchased_items(self, obj):
        return ', '.join([str(item) for item in obj.purchaseditem_set.all()])
