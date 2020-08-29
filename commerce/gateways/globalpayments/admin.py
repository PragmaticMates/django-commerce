from django.contrib import admin

from commerce.gateways.globalpayments.models import Payment, Result


@admin.register(Payment)
class OrderAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    search_fields = ['order__number', 'order__user__email', 'order__user__first_name', 'order__user__last_name', 'order__delivery_name', 'order__delivery_street', 'order__delivery_postcode',
                     'order__delivery_city', 'order__delivery_country']
    list_display = ('id', 'status', 'get_order_display', 'order_number', 'order_status', 'created', 'modified')
    list_select_related = ['order', 'order__user']
    list_filter = ['status', 'order__status']
    autocomplete_fields = ['order']
    readonly_fields = ['created', 'modified']
    ordering = ['-created']

    def order_number(self, obj):
        return obj.order.number

    def order_status(self, obj):
        return obj.order.get_status_display()

    def get_order_display(self, obj):
        return obj.order.get_total_display()


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('id', 'ordernumber', 'merordernum', 'user', 'prcode', 'srcode', 'resulttext', 'is_valid', 'created')
    list_select_related = ['payment__order__user', 'payment__order__payment_method']
    list_filter = ['prcode', 'srcode', 'resulttext']
    autocomplete_fields = ['payment']
    readonly_fields = ['created', 'modified']
    ordering = ['-created']

    def user(self, obj):
        return obj.payment.order.user
