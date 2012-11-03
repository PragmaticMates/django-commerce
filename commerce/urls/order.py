from django.conf.urls import patterns, url

from commerce.views.order import YourOrdersView, InvoiceView


urlpatterns = patterns(
    '',
    url(r'invoice/(?P<pk>[-\d]+)/$',
        InvoiceView.as_view(), name='commerce_orders_invoice'),
    url(r'$', YourOrdersView.as_view(), name='commerce_orders_your'),
)
