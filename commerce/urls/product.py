from django.conf.urls import patterns, url

from commerce.views.product import DetailView


urlpatterns = patterns(
    '',
    url(r'^(?P<slug>[-\w]+)/$', DetailView.as_view(),
        name='commerce_products_detail'),
)
