from decimal import Decimal

import requests
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import EMPTY_VALUES
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from internationalflavor.countries._cldr_data import COUNTRY_NAMES
from modeltrans.admin import ActiveLanguageMixin

from commerce.loyalty import send_loyalty_reminder
from commerce.models import Cart, Item, ShippingOption, PaymentMethod, Order, PurchasedItem, Option, Discount, Supply
from commerce import settings as commerce_settings


if not admin.site.is_registered(ContentType):
    @admin.register(ContentType)
    class ContentTypeAdmin(admin.ModelAdmin):
        search_fields = ['app_label', 'model']


class ItemInline(admin.StackedInline):
    model = Item
    extra = 1


class SupplyInline(GenericTabularInline):
    model = Supply
    extra = 1
    inlines = None


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'items', 'discount', 'total', 'delivery_country', 'created', 'modified', 'open')
    list_select_related = ['user', 'discount']
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


@admin.register(ShippingOption)
class ShippingAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    list_display = ('id', 'title_i18n', 'fee', 'country_names')

    def country_names(self, obj):
        # return ', '.join([f'{c} - {str(COUNTRY_NAMES[c])}' for c in obj.countries])
        return mark_safe('<br>'.join([f'{c} - {str(COUNTRY_NAMES[c])}' for c in obj.countries]))


@admin.register(PaymentMethod)
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
    actions = ['sync_transactions', 'create_invoice', 'send_details', 'send_reminder', 'send_loyalty_reminder']
    date_hierarchy = 'created'
    search_fields = ['number', 'user__email', 'user__first_name', 'user__last_name', 'delivery_name', 'delivery_street', 'delivery_postcode', 'delivery_city', 'delivery_country']
    list_display = ('number', 'status', 'delivery_address', 'purchased_items', 'total', 'delivery_country', 'shipping_option', 'payment_method', 'created', 'modified')
    list_editable = ['status']
    list_select_related = ['user', 'shipping_option', 'payment_method']
    list_filter = ['shipping_option', 'payment_method', 'status', 'reminder_sent']
    inlines = [PurchasedItemInline]
    fieldsets = [
        (None, {'fields': ['user', 'status', 'number']}),
        (_('Delivery address'), {'fields': [('delivery_name', 'delivery_street', 'delivery_postcode', 'delivery_city', 'delivery_country')]}),
        (_('Billing address'), {'fields': [('billing_name', 'billing_street', 'billing_postcode', 'billing_city', 'billing_country')]}),
        (_('Billing details'), {'fields': [('reg_id', 'tax_id', 'vat_id')]}),
        (_('Contact details'), {'fields': [('email', 'phone')]}),
        (_('Shipping'), {'fields': ['shipping_option', 'shipping_fee', 'payment_method', 'payment_fee']}),
        (_('Billing'), {'fields': ['invoices']}),
        (_('Timestamps'), {'fields': ['reminder_sent', 'created', 'modified']}),
    ]
    autocomplete_fields = ['invoices']
    readonly_fields = ['created', 'modified']
    ordering = ['-number']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('purchaseditem_set', 'invoices')

    def delivery_address(self, obj):
        return mark_safe('<br>'.join([str(item) for item in [
            obj.delivery_name,
            obj.delivery_street,
            obj.delivery_postcode,
            obj.delivery_city,
            obj.get_delivery_country_display(),
        ]]))

    def purchased_items(self, obj):
        return ', '.join([str(item) for item in obj.purchaseditem_set.all()])

    def sync_transactions(self, request, queryset):
        if commerce_settings.BANK_API_TOKEN in EMPTY_VALUES:
            messages.error(request, _('Missing bank API token'))
            return

        if commerce_settings.BANK_API in EMPTY_VALUES:
            messages.error(request, _('Missing bank API'))
            return

        transactions = []

        if commerce_settings.BANK_API == 'FIO':
            date_from = '1993-01-01'
            date_to = '2993-12-31'  # TODO
            url = f'https://www.fio.cz/ib_api/rest/periods/{commerce_settings.BANK_API_TOKEN}/{date_from}/{date_to}/transactions.json'
            r = requests.get(url)
            data = r.json()
            transaction_list = data['accountStatement']['transactionList']['transaction']

            mapping = {
                'date': 'column0',  # Datum
                'value': 'column1',  # Objem
                'sender': 'column10',  # Název protiúčtu
                'sender_bank': 'column12',  # Název banky
                'sender_account': 'column2',  # Protiúčet
                'currency': 'column14',  # Měna
                'information': 'column16',  # Zpráva pro příjemce
                'variable_symbol': 'column5',  # VS
                'type': 'column8',  # Typ
                'issued_by': 'column9',  # Provedl
            }

            for t in transaction_list:
                transaction = {}

                for key, column in mapping.items():
                    value = t[column]['value'] if t[column] is not None else None
                    transaction[key] = Decimal(str(value)) if key == 'value' else value

                transactions.append(transaction)

        else:
            messages.error(request, _(f'Bank API {commerce_settings.BANK_API} not implemented'))
            return

        numbers_of_selected_orders = list(queryset.values_list('number', flat=True))

        transactions = list(filter(lambda tr: str(tr['variable_symbol']) in list(map(str, numbers_of_selected_orders)), transactions))

        for transaction in transactions:
            transaction['errors'] = []

            variable_symbol = transaction['variable_symbol']

            if variable_symbol and variable_symbol.isdigit():
                variable_symbol = int(variable_symbol)

                try:
                    order = Order.objects.get(number=variable_symbol)
                except ObjectDoesNotExist:
                    transaction['errors'].append(_('Order not found'))
                    continue

                transaction['order'] = order
                transaction['order_status_before'] = order.status
                transaction['order_status_before_display'] = order.get_status_display()
                transaction['order_status_after'] = order.status
                transaction['order_status_after_display'] = order.get_status_display()

                if order in queryset and order.status == Order.STATUS_AWAITING_PAYMENT:
                    if transaction['currency'] != commerce_settings.CURRENCY:
                        transaction['errors'].append(_('Currency mismatch'))
                    elif transaction['value'] != order.total:
                        transaction['errors'].append(_('Total value mismatch'))
                    else:
                        order.status = Order.STATUS_PAYMENT_RECEIVED
                        order.save(update_fields=['status'])
                        transaction['order_status_after'] = order.status
                        transaction['order_status_after_display'] = order.get_status_display()
            else:
                transaction['errors'].append(_('Missing variable symbol'))

        return render(request, 'commerce/admin/sync_transactions.html', context={'transactions': transactions})
    sync_transactions.short_description = _('Sync transactions')

    def create_invoice(self, request, queryset):
        for obj in queryset:
            obj.create_invoice()
    create_invoice.short_description = _('Create invoice')

    def send_details(self, request, queryset):
        for obj in queryset:
            obj.send_details()
    send_details.short_description = _('Send details')

    def send_reminder(self, request, queryset):
        for obj in queryset:
            obj.send_reminder(force=True)
    send_reminder.short_description = _('Send reminder')

    def send_loyalty_reminder(self, request, queryset):
        if not commerce_settings.LOYALTY_PROGRAM_ENABLED:
            messages.error(request, _('Loyalty program is disabled'))
            return

        counter = 0

        users = get_user_model().objects.filter(id__in=queryset.values('user')).distinct()

        for user in users:
            result = send_loyalty_reminder(user)

            if result is not None:
                counter += 1
                user, points = result
                messages.success(request, _(f'User %s has %d loyalty points') % (user, points))

        messages.info(request, _('Loyalty reminder sent to %d users') % counter)
    send_loyalty_reminder.short_description = _('Send loyalty reminder')


class DiscountValidListFilter(admin.SimpleListFilter):
    title = _('valid')
    parameter_name = 'valid'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('yes')),
            ('no', _('no')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.valid()

        if self.value() == 'no':
            return queryset.not_valid()


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    search_fields = ['code']
    list_display = ('code', 'usage', 'description', 'amount', 'unit', 'valid_until', 'promoted', 'add_to_cart', 'product_types', 'products_qs', 'is_used_in_order')
    list_filter = ['unit', 'usage', 'promoted', 'add_to_cart', DiscountValidListFilter]
    autocomplete_fields = ['content_types', 'user']

    def product_types(self, obj):
        return ', '.join([str(type) for type in obj.content_types.all()])

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('content_types', 'products')
        # TODO: annotate is_used_in_order

    def products_qs(self, obj):
        return ', '.join([str(product) for product in obj.products.all()])
    products_qs.short_description = _('Products')


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    date_hierarchy = 'datetime'
    list_display = ('datetime', 'real_product', 'quantity')
    autocomplete_fields = ['content_type']


@admin.register(PurchasedItem)
class PurchasedItemAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    search_fields = ['order__number', 'order__user__email', 'order__user__first_name', 'order__user__last_name', 'order__delivery_name', 'order__delivery_street', 'order__delivery_postcode', 'order__delivery_city', 'order__delivery_country']
    list_display = ('id', '__str__', 'get_subtotal_display', 'order_number', 'order_status', 'option', 'created', 'modified')
    list_select_related = ['order', 'order__user', 'option']
    list_filter = ['order__status', 'option']
    autocomplete_fields = ['order']
    readonly_fields = ['created', 'modified']

    def order_number(self, obj):
        return obj.order.number
    
    def order_status(self, obj):
        return obj.order.get_status_display()
