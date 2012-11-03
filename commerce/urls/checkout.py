from django.conf.urls import patterns, url

from commerce.views.checkout import LoginRegisterView, ShippingPaymentView, \
    ConfirmView, ProfileView


urlpatterns = patterns(
    '',
    url(r'login-register/$',
        LoginRegisterView.as_view(), name='commerce_checkout_login_register'),
    url(r'profile/$',
        ProfileView.as_view(), name='commerce_checkout_profile'),
    url(r'shipping-payment/$',
        ShippingPaymentView.as_view(),
        name='commerce_checkout_shipping_payment'),
    url(r'confirm/$',
        ConfirmView.as_view(), name='commerce_checkout_confirm'),
)
