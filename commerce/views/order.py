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

        # http://127.0.0.1:8002/sk/obchod/order/1028/payment/return/?OPERATION=CREATE_ORDER&ORDERNUMBER=2&PRCODE=0&SRCODE=0&RESULTTEXT=OK&DIGEST=bzxeV3DDq7wUd%2F1TE2NR4GQJx62znQPYFvjoYSCe5Jj%2B%2FKpxpM%2BNn28bFDpvZ6ISCWzTPTTNhRyjdGlr2u1WDclce7N8jzSXzqO13bJ46wKjAbKRKKmWIRkKxIcY5HWI%2Bey02FlUGyVZbUVyUzFLQjtS%2FVPps4ww3MdvddRpXaS1Wg72Y%2F0mf0CR7T%2B24NnHL8RaU6pRpARMRhIZ9WQ8n%2BMz2buuvqce81LUZYisLQOLENieVoXxFvAkTUjxuujCAIDe8Vv1oWaLUMVSaoErxbP28F6JhGE2kAl4AiAFVHH8ucKixxSOkGFwsI0DNU3McpLVdDtw%2BL4PpXveCLqQRQ%3D%3D&DIGEST1=fO8DUdIfZo3%2B2g9EZlLHNQbdQl71O0zrpZ%2FhPnIceh3eYxowX%2B%2FZeaPIYclkR9eS0QsC1Pyy68qjSSRK3KRQQdG7Lp1Y5BVIX3Bv98fyFZQZWuhkMDilh6PPakCG9PSbCDxGxwNqDyd9qB2O%2F%2BgeJcL4SGS%2FIyEVZIkRAuXLKp%2BTv%2FkF%2BJcDmQOvAn619YBd5XvypyJvWJIW%2BsRncTDMuKlAHb9wY%2F8TGBSW5cEUmEjSloxgZmj2B4a4REol57I2Y%2BmbgnfkVfvnta35p1Oaew7yImW%2F7PjeO4vWk9cundfS7hLov374R6XZZ3vUlIrgrfk3VxvOgb70X45%2F%2B%2FjrMw%3D%3D
        # GET:
        # <QueryDict: {'OPERATION': ['CREATE_ORDER'], 'ORDERNUMBER': ['2'], 'PRCODE': ['0'], 'SRCODE': ['0'], 'RESULTTEXT': ['OK'], 'DIGEST': ['bzxeV3DDq7wUd/1TE2NR4GQJx62znQPYFvjoYSCe5Jj+/KpxpM+Nn28bFDpvZ6ISCWzTPTTNhRyjdGlr2u1WDclce7N8jzSXzqO13bJ46wKjAbKRKKmWIRkKxIcY5HWI+ey02FlUGyVZbUVyUzFLQjtS/VPps4ww3MdvddRpXaS1Wg72Y/0mf0CR7T+24NnHL8RaU6pRpARMRhIZ9WQ8n+Mz2buuvqce81LUZYisLQOLENieVoXxFvAkTUjxuujCAIDe8Vv1oWaLUMVSaoErxbP28F6JhGE2kAl4AiAFVHH8ucKixxSOkGFwsI0DNU3McpLVdDtw+L4PpXveCLqQRQ=='], 'DIGEST1': ['fO8DUdIfZo3+2g9EZlLHNQbdQl71O0zrpZ/hPnIceh3eYxowX+/ZeaPIYclkR9eS0QsC1Pyy68qjSSRK3KRQQdG7Lp1Y5BVIX3Bv98fyFZQZWuhkMDilh6PPakCG9PSbCDxGxwNqDyd9qB2O/+geJcL4SGS/IyEVZIkRAuXLKp+Tv/kF+JcDmQOvAn619YBd5XvypyJvWJIW+sRncTDMuKlAHb9wY/8TGBSW5cEUmEjSloxgZmj2B4a4REol57I2Y+mbgnfkVfvnta35p1Oaew7yImW/7PjeO4vWk9cundfS7hLov374R6XZZ3vUlIrgrfk3VxvOgb70X45/+/jrMw==']}>
        # TODO: validation of signature

        # result data
        ORDERNUMBER = request.GET.get('ORDERNUMBER', None)
        PRCODE = request.GET.get('PRCODE', None)
        RESULTTEXT = request.GET.get('RESULTTEXT', None)

        # check primary result code
        if PRCODE != '0':
            messages.error(request, '{} {}'.format(_('Payment failed. Error detail:'), RESULTTEXT))
            return redirect('commerce:orders')

        # check if order order/transaction id is correct
        if not order.order_set.filter(id=int(ORDERNUMBER)).exists():
            messages.error(request, _('Transaction not recognised'))
            return redirect('commerce:orders')

        if RESULTTEXT == 'OK':
            from commerce.gateways.globalpayments.models import Order as GPOrder
            gporder = GPOrder.objects.get(pk=int(ORDERNUMBER))
            gporder.status = GPOrder.STATUS_PAID
            gporder.save(update_fields=['status'])

            if order.status == Order.STATUS_AWAITING_PAYMENT:
                order.status = Order.STATUS_PAYMENT_RECEIVED
                order.save(update_fields=['status'])
                messages.success(request, _('Order successfully paid.'))
                return redirect('inventor:accounts:user_dashboard')  # TODO: add new setting: COMMERCE_SUCCESSFUL_PAYMENT_REDIRECT_URL

        return redirect('commerce:orders')


class OrderListView(LoginRequiredMixin, ListView):
    model = Order

    def get_queryset(self):
        return self.request.user.order_set.all().prefetch_related('invoices', 'purchaseditem_set')
