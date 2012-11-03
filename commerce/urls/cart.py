from django.conf.urls import patterns, url

from commerce.views.cart import CartView, BuyView, EmptyView, \
    RemoveView, UpdateView


urlpatterns = patterns(
    '',
    url(r'remove/(?P<pk>[-\d]+)$',
        RemoveView.as_view(), name='commerce_cart_remove'),
    url(r'buy/(?P<pk>[-\d]+)$',
        BuyView.as_view(), name='commerce_cart_buy'),
    url(r'update$', UpdateView.as_view(), name='commerce_cart_update'),
    url(r'empty$', EmptyView.as_view(), name='commerce_cart_empty'),
    url(r'$', CartView.as_view(), name='commerce_cart'),
)
