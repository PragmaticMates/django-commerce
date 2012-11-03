from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.views import flatpage
from django.http import Http404
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _


class FlatpageFallbackMiddleware(object):
    def process_response(self, request, response):
        if response.status_code != 404:
            return response
        try:
            url = request.path_info

            if not url.startswith('/'):
                url = '/' + url

            f = get_object_or_404(
                FlatPage, url__exact=url, sites__id__exact=settings.SITE_ID)

            request.breadcrumbs = (
                {'name': _(u'Home'), 'url': '/'},
                {'name': f.title, 'url': url})

            return flatpage(request, request.path_info)
        # Return the original response if any errors happened. Because this
        # is a middleware, we can't assume the errors will be caught elsewhere.
        except Http404:
            return response
        except:
            if settings.DEBUG:
                raise
            return response
