from django.conf.urls import patterns, url

from commerce.views.catalog import IndexView, DetailView


urlpatterns = patterns(
    '',
    url(r'(?P<slug>[-\w]+)/$', DetailView.as_view(),
        name='commerce_catalogs_detail'),
    url(r'$', IndexView.as_view(), name='commerce_catalogs'),
)
