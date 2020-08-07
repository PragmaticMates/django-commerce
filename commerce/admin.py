import requests
from django.contrib import admin, messages
from django.contrib.contenttypes.admin import GenericStackedInline
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import EMPTY_VALUES
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from internationalflavor.countries._cldr_data import COUNTRY_NAMES
from modeltrans.admin import ActiveLanguageMixin

from commerce.models import Cart, Item, Shipping, Payment, Order, PurchasedItem, Option, Discount, Supply
from commerce import settings as commerce_settings


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
    list_display = ('id', 'title_i18n', 'fee', 'country_names')

    def country_names(self, obj):
        # return ', '.join([f'{c} - {str(COUNTRY_NAMES[c])}' for c in obj.countries])
        return mark_safe('<br>'.join([f'{c} - {str(COUNTRY_NAMES[c])}' for c in obj.countries]))


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
    actions = ['sync_transactions', 'create_invoice', 'send_details', 'send_reminder']
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
        return super().get_queryset(request).prefetch_related('purchaseditem_set')

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
                    transaction[key] = value

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


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'usage', 'description', 'amount', 'valid_until', 'promoted', 'add_to_cart', 'product_types', 'is_used_in_order')
    list_filter = ['usage', 'promoted', 'add_to_cart']
    autocomplete_fields = ['content_types']

    def product_types(self, obj):
        return ', '.join([str(type) for type in obj.content_types.all()])

    # def get_queryset(self, request):
    # TODO: annotate is_used_in_order


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    date_hierarchy = 'datetime'
    list_display = ('datetime', 'real_product', 'quantity')
    autocomplete_fields = ['content_type']
