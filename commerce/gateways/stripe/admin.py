import stripe
from django.contrib import admin
from commerce import settings as commerce_settings
from commerce.gateways.stripe.models import Customer

stripe.api_key = commerce_settings.GATEWAY_STRIPE_SECRET_API_KEY


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('id', 'user', 'stripe_id', 'payment_method', 'created', 'modified')
    list_select_related = ['user']
    autocomplete_fields = ['user']
    readonly_fields = ['created', 'modified']
    ordering = ['-created']
    actions = ['charge']

    def charge(self, request, queryset):
        for customer in queryset:
            # Setup intent: https://stripe.com/docs/payments/save-and-reuse#checkout
            # setup_intent = stripe.SetupIntent.retrieve('ID')

            # Payment intents
            # https://stripe.com/docs/api/payment_intents/object#payment_intent_object-setup_future_usage
            payment_intent = stripe.PaymentIntent.create(
                amount=100,
                currency='eur',
                payment_method_types=['card'],
                customer=customer.stripe_id,
                # payment_method=setup_intent.payment_method,
                payment_method=customer.payment_method,
            )

            # To create a PaymentIntent for confirmation, see our guide at: https://stripe.com/docs/payments/payment-intents/creating-payment-intents#creating-for-automatic
            stripe.PaymentIntent.confirm(payment_intent.id,
                # payment_method="pm_card_visa",
            )

            # SCA
            # https://stripe.com/docs/billing/migration/strong-customer-authentication
