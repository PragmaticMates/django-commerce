from django.contrib import admin

from commerce.gateways.stripe.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('id', 'stripe_id', 'user', 'created', 'modified')
    list_select_related = ['user']
    autocomplete_fields = ['user']
    readonly_fields = ['created', 'modified']
    ordering = ['-created']
