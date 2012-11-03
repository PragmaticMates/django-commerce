from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from commerce.models.account import Profile
from commerce.models.order import Order


class YourOrdersView(ListView):
    model = Order
    template_name = 'commerce/orders/index.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        request.breadcrumbs = (
            {'name': _(u'Home'), 'url': '/'},
            {'name': _(u'My orders'), 'url': reverse('commerce_orders_your')})
        return super(YourOrdersView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Order.objects.all().by_user(self.request.user)


class InvoiceView(DetailView):
    template_name = 'commerce/orders/invoice.html'
    model = Order

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        try:
            self.profile = Profile.objects.get(user=request.user)
        except ObjectDoesNotExist:
            self.profile = None

        return super(InvoiceView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InvoiceView, self).get_context_data(**kwargs)
        context['profile'] = self.profile
        return context
