from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView

from commerce.models import Order


class OrderPaymentView(LoginRequiredMixin, DetailView):
    model = Order
    slug_field = 'number'
    slug_url_kwarg = 'number'

    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()
        raise NotImplementedError()


class OrderListView(LoginRequiredMixin, ListView):
    model = Order

    def get_queryset(self):
        return self.request.user.order_set.all()
