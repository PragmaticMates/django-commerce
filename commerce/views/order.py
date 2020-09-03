from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView

from commerce.models import Order
from commerce import settings as commerce_settings


class OrderPaymentView(LoginRequiredMixin, DetailView):
    """
    Designed for online payments
    """
    model = Order
    slug_field = 'number'
    slug_url_kwarg = 'number'

    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()

        if order.status != Order.STATUS_AWAITING_PAYMENT:
            messages.error(request, _('It is not possible to pay this order anymore.'))
            return redirect(order.get_absolute_url())

        return redirect(order.get_payment_gateway_url())


class OrderPaymentReturnView(LoginRequiredMixin, DetailView):
    model = Order
    slug_field = 'number'
    slug_url_kwarg = 'number'

    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()

        data = request.GET  # TODO: GET or POST?
        success, message = order.payment_manager.handle_payment_result(data)

        if success:
            messages.success(request, message)
            return redirect(commerce_settings.SUCCESSFUL_PAYMENT_REDIRECT_URL)
        else:
            messages.error(request, message)
            return redirect('commerce:orders')  # TODO: add new setting: COMMERCE_FAILED_PAYMENT_REDIRECT_URL


class OrderListView(LoginRequiredMixin, ListView):
    model = Order

    def get_queryset(self):
        return self.request.user.order_set.all().prefetch_related('invoices', 'purchaseditem_set')
