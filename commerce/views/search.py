from django.core.urlresolvers import reverse
from django.views.generic.list import ListView
from django.utils.translation import ugettext_lazy as _

from commerce.models.product import Product
from commerce.app_settings import COMMERCE_PRODUCTS_PER_PAGE


class SearchView(ListView):
    model = Product
    paginate_by = COMMERCE_PRODUCTS_PER_PAGE
    template_name = 'commerce/search/index.html'

    def dispatch(self, request, *args, **kwargs):
        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Search'), 'url': reverse('commerce_search')})
        return super(SearchView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        q = self.request.GET.get('q', None)
        if q is None:
            return Product.objects.none()

        return Product.objects.visible().search(q)
