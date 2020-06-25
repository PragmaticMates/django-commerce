from django.contrib import admin

from commerce.models import Cart, Item


class ItemInline(admin.StackedInline):
    model = Item
    extra = 1


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'items', 'total', 'created', 'modified', 'open')
    list_select_related = ['user']
    inlines = [ItemInline]

    def items(self, obj):
        return ', '.join([str(item) for item in obj.item_set.all()])
