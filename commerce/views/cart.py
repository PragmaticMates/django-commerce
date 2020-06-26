from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import DetailView, UpdateView

from commerce.forms import AddressesForm, ShippingAndPaymentForm
from commerce.models import Cart


class AddToCartView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        content_type = get_object_or_404(ContentType, id=kwargs['content_type_id'])
        product = get_object_or_404(content_type.model_class(), id=kwargs['object_id'])
        cart = Cart.get_for_user(request.user)

        # TODO: settings
        # TODO: check if product can be added multiple times into cart
        # TODO: max items in cart
        ALLOW_MULTIPLE_SAME_ITEMS = False
        MAX_ITEMS = 3

        if cart.total_items >= MAX_ITEMS:
            messages.warning(request, _(f'You can order at most {MAX_ITEMS} items at once'))
        else:
            if ALLOW_MULTIPLE_SAME_ITEMS or not cart.has_item(product):
                cart.add_item(product)
                messages.info(request, _(f'{product} was added into cart'))
            else:
                messages.warning(request, _(f'{product} is already in cart'))

        back_url = request.GET.get('back_url', cart.get_absolute_url())
        return redirect(back_url)


class CartDetailView(LoginRequiredMixin, DetailView):
    model = Cart

    def get_object(self, queryset=None):
        return self.model.get_for_user(self.request.user)


class CheckoutAddressesView(LoginRequiredMixin, UpdateView):
    model = Cart
    template_name = 'commerce/checkout.html'
    form_class = AddressesForm

    def get_object(self, queryset=None):
        return self.model.get_for_user(self.request.user)

    def get_initial(self):
        user = self.object.user
        last_user_order = user.order_set.last()

        if last_user_order:
            return {
                'delivery_name': last_user_order.delivery_name,
                'delivery_street': last_user_order.delivery_street,
                'delivery_postcode': last_user_order.delivery_postcode,
                'delivery_city': last_user_order.delivery_city,
                'delivery_country': last_user_order.delivery_country,
                'billing_name': last_user_order.billing_name,
                'billing_street': last_user_order.billing_street,
                'billing_postcode': last_user_order.billing_postcode,
                'billing_city': last_user_order.billing_city,
                'billing_country': last_user_order.billing_country,
                'reg_id': last_user_order.reg_id,
                'tax_id': last_user_order.tax_id,
                'vat_id': last_user_order.vat_id,
                'email': last_user_order.email,
                'phone': last_user_order.phone,
            }
        else:
            return {
                'delivery_name': user.get_full_name(),
                'delivery_street': user.street,
                'delivery_postcode': user.postcode,
                'delivery_city': user.city,
                'delivery_country': user.country,
                'billing_name': user.get_full_name(),
                'billing_street': user.street,
                'billing_postcode': user.postcode,
                'billing_city': user.city,
                'billing_country': user.country,
                'email': user.email,
                'phone': user.phone,
            }

    def form_valid(self, form):
        form.save()
        return redirect('commerce:checkout_shipping_and_payment')


class CheckoutShippingAndPaymentView(LoginRequiredMixin, UpdateView):
    model = Cart
    template_name = 'commerce/checkout.html'
    form_class = ShippingAndPaymentForm

    def get_object(self, queryset=None):
        return self.model.get_for_user(self.request.user)

    def form_valid(self, form):
        form.save()
        return redirect('commerce:checkout_payment')
