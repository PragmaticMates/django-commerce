from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import DetailView, UpdateView

from commerce.forms import AddressesForm, ShippingAndPaymentForm
from commerce.models import Cart, Order, Payment


class AddToCartView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        content_type = get_object_or_404(ContentType, id=kwargs['content_type_id'])
        product = get_object_or_404(content_type.model_class(), id=kwargs['object_id'])
        cart = Cart.get_for_user(request.user)

        # TODO: settings
        # TODO: check if product can be added multiple times into cart
        # TODO: max items in cart
        ALLOW_MULTIPLE_SAME_ITEMS = False
        MAX_ITEMS = 3

        if cart.items_quantity >= MAX_ITEMS:
            messages.warning(request, _(f'You can order at most {MAX_ITEMS} items at once'))
        else:
            if ALLOW_MULTIPLE_SAME_ITEMS or not cart.has_item(product):
                cart.add_item(product)
                messages.info(request, _(f'{product} was added into cart'))
            else:
                messages.warning(request, _(f'{product} is already in cart'))

        back_url = request.GET.get('back_url', cart.get_absolute_url())
        return redirect(back_url)


class CartMixin(LoginRequiredMixin):
    model = Cart

    def get_object(self, queryset=None):
        return self.model.get_for_user(self.request.user)


class CartDetailView(CartMixin, DetailView):
    pass


class EmptyCartRedirectMixin(object):
    def dispatch(self, request, *args, **kwargs):
        cart = self.get_object()

        if cart.is_empty():
            return redirect(cart.get_absolute_url())

        return super().dispatch(request, *args, **kwargs)


class CheckoutAddressesView(CartMixin, EmptyCartRedirectMixin, UpdateView):
    template_name = 'commerce/checkout_form.html'
    form_class = AddressesForm

    def get_initial(self):
        initial = super().get_initial()
        user = self.object.user
        last_user_order = user.order_set.last()

        # TODO: refactor
        if last_user_order:
            initial.update({
                'delivery_name': self.object.delivery_name or last_user_order.delivery_name,
                'delivery_street': self.object.delivery_street or last_user_order.delivery_street,
                'delivery_postcode': self.object.delivery_postcode or last_user_order.delivery_postcode,
                'delivery_city': self.object.delivery_city or last_user_order.delivery_city,
                'delivery_country': self.object.delivery_country or last_user_order.delivery_country,
                'billing_name': self.object.billing_name or last_user_order.billing_name,
                'billing_street': self.object.billing_street or last_user_order.billing_street,
                'billing_postcode': self.object.billing_postcode or last_user_order.billing_postcode,
                'billing_city': self.object.billing_city or last_user_order.billing_city,
                'billing_country': self.object.billing_country or last_user_order.billing_country,
                'reg_id': self.object.reg_id or last_user_order.reg_id,
                'tax_id': self.object.tax_id or last_user_order.tax_id,
                'vat_id': self.object.vat_id or last_user_order.vat_id,
                'email': self.object.email or last_user_order.email,
                'phone': self.object.phone or last_user_order.phone,
            })
        else:
            initial.update({
                'delivery_name': self.object.delivery_name or user.get_full_name(),
                'delivery_street': self.object.delivery_street or user.street,
                'delivery_postcode': self.object.delivery_postcode or user.postcode,
                'delivery_city': self.object.delivery_city or user.city,
                'delivery_country': self.object.delivery_country or user.country,
                'billing_name': self.object.billing_name or user.get_full_name(),
                'billing_street': self.object.billing_street or user.street,
                'billing_postcode': self.object.billing_postcode or user.postcode,
                'billing_city': self.object.billing_city or user.city,
                'billing_country': self.object.billing_country or user.country,
                'email': self.object.email or user.email,
                'phone': self.object.phone or user.phone,
            })

        return initial

    def form_valid(self, form):
        form.save()
        return redirect('commerce:checkout_shipping_and_payment')


class CheckoutShippingAndPaymentView(CartMixin, EmptyCartRedirectMixin, UpdateView):
    template_name = 'commerce/checkout_form.html'
    form_class = ShippingAndPaymentForm

    def form_valid(self, form):
        form.save()
        return redirect('commerce:checkout_summary')


class CheckoutSummaryView(CartMixin, EmptyCartRedirectMixin, DetailView):
    template_name = 'commerce/checkout_summary.html'


class CheckoutFinishView(CartMixin, DetailView):
    def get(self, request, *args, **kwargs):
        # TODO: default order status / status by cart / items ...
        cart = self.get_object()
        order_status = Order.STATUS_AWAITING_PAYMENT

        if cart.can_be_finished():
            order = cart.to_order(status=order_status)

            if not order.payment_method:
                messages.error(request, _('Missing payment method'))
                return redirect(order.get_absolute_url())

            if order.payment_method.method == Payment.METHOD_ONLINE_PAYMENT:
                return redirect(order.get_payment_url())

            return redirect(order.get_absolute_url())
        else:
            messages.warning(request, _('Checkout process can not be finished yet'))
            return redirect(cart.get_absolute_url())
