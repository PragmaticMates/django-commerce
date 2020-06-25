from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from commerce.models import Cart, Item


class ItemInline(admin.StackedInline):
    model = Item
    extra = 1


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'items', 'total', 'created', 'modified', 'open')
    list_select_related = ['user']
    inlines = [ItemInline]
    fieldsets = [
        (None, {'fields': ['user']}),
        (_('Delivery address'), {'fields': [('delivery_name', 'delivery_street', 'delivery_postcode', 'delivery_city', 'delivery_country')]}),
        (_('Billing address'), {'fields': [('billing_name', 'billing_street', 'billing_postcode', 'billing_city', 'billing_country')]}),
        (_('Billing details'), {'fields': [('reg_id', 'tax_id', 'vat_id')]}),
        (_('Contact details'), {'fields': [('email', 'phone')]}),
        (_('Timestamps'), {'fields': ['created', 'modified']}),
    ]
    readonly_fields = ['created', 'modified']

    def items(self, obj):
        return ', '.join([str(item) for item in obj.item_set.all()])
