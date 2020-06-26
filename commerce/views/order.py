from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from commerce.models import Order


class OrderPaymentView(LoginRequiredMixin, DetailView):
    model = Order
    slug_field = 'number'
    slug_url_kwarg = 'number'

    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()
        print(order)
        raise NotImplementedError()
