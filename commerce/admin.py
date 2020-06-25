from django.contrib import admin
from commerce.models import Cart


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user',)
    list_select_related = ['user']
