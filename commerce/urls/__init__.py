from django.conf import settings
from django.conf.urls import patterns, include, url

from commerce.views.catalog import IndexView
from commerce.views.search import SearchView

urlpatterns = patterns(
    '',
    url(r'^orders/', include('commerce.urls.order')),
    url(r'^checkout/', include('commerce.urls.checkout')),
    url(r'^catalogs/', include('commerce.urls.catalog')),
    url(r'^products/', include('commerce.urls.product')),
    url(r'^cart/', include('commerce.urls.cart')),
    url(r'^accounts/', include('commerce.urls.account')),
    url(r'^search/$', SearchView.as_view(), name='commerce_search'),
    url(r'^$', IndexView.as_view(), name='home'),
)

urlpatterns += patterns(
    '',
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT,
        }, name='media'),
)
