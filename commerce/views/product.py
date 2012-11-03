from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from commerce.models.product import Product


class DetailView(DetailView):
    model = Product
    template_name = 'commerce/products/detail.html'

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, slug=kwargs.get('slug'))

        url_catalog = reverse(
            'commerce_catalogs_detail',
            args=[self.product.catalog.slug, ])

        url_product = reverse(
            'commerce_products_detail',
            args=[self.product.slug, ])

        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'Catalogs'), 'url': reverse('commerce_catalogs')},
            {'name': self.product.catalog.title, 'url': url_catalog},
            {'name': self.product.title, 'url': url_product})

        self.product.views += 1
        self.product.save()

        return super(DetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['object_list'] = self.product.get_associated_products()
        return context
