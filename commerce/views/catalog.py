from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic.list import ListView

from commerce.app_settings import COMMERCE_PRODUCTS_PER_PAGE
from commerce.models.catalog import Catalog
from commerce.models.product import Product
from commerce.forms.filter import FilterForm

class IndexView(ListView):
    model = Catalog
    template_name = 'commerce/catalogs/index.html'

    def dispatch(self, request, *args, **kwargs):
        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Catalogs'), 'url': reverse('commerce_catalogs')})
        return super(IndexView, self).dispatch(request, *args, **kwargs)


class DetailView(ListView):
    model = Product
    template_name = 'commerce/catalogs/detail.html'
    paginate_by = COMMERCE_PRODUCTS_PER_PAGE

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Catalog, slug=kwargs.get('slug'))
        self.request = request
        url = reverse('commerce_catalogs_detail', args=[self.object.slug, ])

        if 'paginate_by' in request.GET:
            self.paginate_by = request.GET.get(
                'paginate_by', COMMERCE_PRODUCTS_PER_PAGE)

        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Catalogs'), 'url': reverse('commerce_catalogs')},
            {'name': self.object.title, 'url': url})

        return super(DetailView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = self.object.get_products()

        for property in self.request.GET.getlist('properties'):
            if property == FilterForm.PROPERTY_TOP:
                qs = qs.filter(is_top=True)
            if property == FilterForm.PROPERTY_NEW:
                qs = qs.filter(is_new=True)
            if property == FilterForm.PROPERTY_DISCOUNT:
                qs = qs.filter(price_discount__isnull=False)

        if 'sort' in self.request.GET:
            ordering = ''
            if 'ordering' in self.request.GET:
                if self.request.GET['ordering'] == FilterForm.DESC:
                    ordering = '-'

            sort = self.request.GET.get('sort', FilterForm.SORT_TITLE)
            if sort == FilterForm.SORT_DATE:
                return qs.order_by(ordering + 'created')
            elif sort == FilterForm.SORT_PRICE:
                return qs.order_by(ordering + 'price_real')
            else:
                return qs.order_by(ordering + 'created')

        return qs

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['object'] = self.object
        return context
