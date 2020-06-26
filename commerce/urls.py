from django.urls import path
from django.utils.translation import pgettext_lazy
from commerce.views.cart import AddToCartView, CartDetailView, CheckoutAddressesView, \
    CheckoutShippingAndPaymentView, CheckoutSummaryView, CheckoutFinishView
from commerce.views.order import OrderPaymentView

app_name = 'commerce'

urlpatterns = [
    path(pgettext_lazy("url", 'add-to-cart/<int:content_type_id>/<int:object_id>/'), AddToCartView.as_view(), name='add_to_cart'),
    path(pgettext_lazy("url", 'cart/'), CartDetailView.as_view(), name='cart'),
    path(pgettext_lazy("url", 'checkout/addresses/'), CheckoutAddressesView.as_view(), name='checkout_addresses'),
    path(pgettext_lazy("url", 'checkout/shipping-and-payment/'), CheckoutShippingAndPaymentView.as_view(), name='checkout_shipping_and_payment'),
    path(pgettext_lazy("url", 'checkout/summary/'), CheckoutSummaryView.as_view(), name='checkout_summary'),
    path(pgettext_lazy("url", 'checkout/finish/'), CheckoutFinishView.as_view(), name='checkout_finish'),
    path(pgettext_lazy("url", 'order/<int:number>/payment/'), OrderPaymentView.as_view(), name='order_payment'),
]
