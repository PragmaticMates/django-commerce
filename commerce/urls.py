from django.conf import settings
from django.urls import path
from django.utils.translation import pgettext_lazy
from commerce.views.cart import AddToCartView, RemoveFromCartView, CartDetailView, CheckoutAddressesView, \
    CheckoutShippingAndPaymentView, CheckoutSummaryView, CheckoutFinishView, UnapplyDiscountCartView
from commerce.views.order import OrderPaymentView, OrderPaymentReturnView, OrderListView
from commerce.views.loyalty import LoyaltyProgramView
from commerce import settings as commerce_settings
from commerce.gateways.stripe.views import StripeCreateSessionView, StripeSuccessPaymentView, StripeCancelPaymentView, StripeWebhookView

app_name = 'commerce'

urlpatterns = [
    path(pgettext_lazy("url", 'add-to-cart/<int:content_type_id>/<int:object_id>/'), AddToCartView.as_view(), name='add_to_cart'),
    path(pgettext_lazy("url", 'remove-from-cart/<int:item_id>/'), RemoveFromCartView.as_view(), name='remove_from_cart'),
    path(pgettext_lazy("url", 'unapply-discount/'), UnapplyDiscountCartView.as_view(), name='unapply_discount'),
    path(pgettext_lazy("url", 'cart/'), CartDetailView.as_view(), name='cart'),
    path(pgettext_lazy("url", 'checkout/addresses/'), CheckoutAddressesView.as_view(), name='checkout_addresses'),
    path(pgettext_lazy("url", 'checkout/shipping-and-payment/'), CheckoutShippingAndPaymentView.as_view(), name='checkout_shipping_and_payment'),
    path(pgettext_lazy("url", 'checkout/summary/'), CheckoutSummaryView.as_view(), name='checkout_summary'),
    path(pgettext_lazy("url", 'checkout/finish/'), CheckoutFinishView.as_view(), name='checkout_finish'),
    path(pgettext_lazy("url", 'order/<int:number>/payment/'), OrderPaymentView.as_view(), name='order_payment'),
    path(pgettext_lazy("url", 'order/<int:number>/payment/return/'), OrderPaymentReturnView.as_view(), name='order_payment_return'),
    path(pgettext_lazy("url", 'orders/'), OrderListView.as_view(), name='orders'),
]

if 'commerce.gateways.stripe' in settings.INSTALLED_APPS:
    urlpatterns += [
        path(pgettext_lazy("url", 'stripe/create-session/<int:pk>/'), StripeCreateSessionView.as_view(), name='stripe_create_session'),
        path(pgettext_lazy("url", 'stripe/success/'), StripeSuccessPaymentView.as_view(), name='stripe_success_payment'),
        path(pgettext_lazy("url", 'stripe/cancel/'), StripeCancelPaymentView.as_view(), name='stripe_cancel_payment'),
        path(pgettext_lazy("url", 'stripe/webhook/'), StripeWebhookView.as_view(), name='stripe_webhook'),
    ]

if commerce_settings.LOYALTY_PROGRAM_ENABLED:
    urlpatterns += [
        path(pgettext_lazy("url", 'loyalty-program/'), LoyaltyProgramView.as_view(), name='loyalty'),
    ]
