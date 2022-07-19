from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.validators import EMPTY_VALUES
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import DetailView, UpdateView

from commerce import settings as commerce_settings
from commerce.forms import AddressesForm, ShippingAndPaymentForm, DiscountCodeForm
from commerce.models import Cart, Order, PaymentMethod, Item, Option, ShippingOption
from commerce.templatetags.commerce import discount_for_product


class AddToCartView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        content_type = get_object_or_404(ContentType, id=kwargs['content_type_id'])
        product = get_object_or_404(content_type.model_class(), id=kwargs['object_id'])
        option = get_object_or_404(Option, slug_i18n=request.GET['option']) if 'option' in request.GET else None
        cart = Cart.get_for_user(request.user)

        # TODO: settings:
        # TODO: check if product can be added multiple times into cart
        # TODO: max items in cart
        ALLOW_MULTIPLE_SAME_ITEMS = False
        MAX_ITEMS = 3

        if cart.items_quantity >= MAX_ITEMS:
            messages.warning(request, _(f'You can order at most %d items at once') % MAX_ITEMS)
        else:
            if ALLOW_MULTIPLE_SAME_ITEMS or not cart.has_item(product, option):
                # add item into cart
                cart.add_item(product, option)

                # discount
                removed_cart_discount = None

                if cart.discount:
                    # remove discount if it is not valid anymore
                    if not cart.discount.can_be_used_in_cart(cart):
                        removed_cart_discount = cart.discount
                        cart.discount = None
                        cart.save(update_fields=['discount'])
                else:
                    # if no discount is applied yet, check if there is a valid discount available for product
                    self.apply_discount_by_product(cart, product)

                if removed_cart_discount is not None:
                    messages.warning(request, _('Discount %s was removed from cart') % removed_cart_discount)

                messages.info(request, _('%s was added into cart') % product)
            else:
                messages.warning(request, _('%s is already in cart') % product)

        back_url = request.GET.get('back_url', cart.get_absolute_url())
        return redirect(back_url)

    def apply_discount_by_product(self, cart, product):
        discount = discount_for_product({'request': self.request}, product)

        if discount and discount.add_to_cart:
            cart.discount = discount
            cart.save(update_fields=['discount'])


class UnapplyDiscountCartView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        cart = Cart.get_for_user(request.user)
        cart.discount = None
        cart.save(update_fields=['discount'])
        back_url = request.GET.get('back_url', cart.get_absolute_url())
        return redirect(back_url)


class RemoveFromCartView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        item = get_object_or_404(Item, id=kwargs['item_id'])
        cart = Cart.get_for_user(request.user)

        if item in cart.item_set.all():
            item.quantity -= 1
            item.save(update_fields=['quantity'])
            if item.quantity <= 0:
                item.delete()
            messages.info(request, _('%s removed from cart') % item)

        # discount
        if cart.discount:
            # remove discount if it is not valid anymore
            if not cart.discount.is_valid:
                cart.discount = None
                cart.save(update_fields=['discount'])

        # unset loyalty points
        if cart.subtotal < 0 < cart.loyalty_points:
            cart.update_loyalty_points()

        # delete empty cart
        if not cart.item_set.exists():
            cart.delete()

        back_url = request.GET.get('back_url', cart.get_absolute_url())
        return redirect(back_url)


class CartMixin(LoginRequiredMixin):
    model = Cart

    def get_object(self, queryset=None):
        return self.model.get_for_user(self.request.user)


class CartDetailView(CartMixin, UpdateView):
    form_class = DiscountCodeForm
    template_name = 'commerce/cart_detail.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            'loyalty_program_enabled': commerce_settings.LOYALTY_PROGRAM_ENABLED,
        })
        return context_data

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update({
            'user': self.request.user
        })
        return form_kwargs


class EmptyCartRedirectMixin(object):
    def dispatch(self, request, *args, **kwargs):
        cart = self.get_object()

        if cart.is_empty():
            return redirect(cart.get_absolute_url())

        return super().dispatch(request, *args, **kwargs)


class CheckoutAddressesView(CartMixin, EmptyCartRedirectMixin, UpdateView):
    template_name = 'commerce/checkout_form.html'
    form_class = AddressesForm

    def get_cart_details(self, subject):
        if hasattr(subject, 'get_cart_details'):
            details = subject.get_cart_details()
        else:
            details = {
                'delivery_name': subject.delivery_name,
                'delivery_street': subject.delivery_street,
                'delivery_postcode': subject.delivery_postcode,
                'delivery_city': subject.delivery_city,
                'delivery_country': subject.delivery_country,
                'billing_name': subject.billing_name,
                'billing_street': subject.billing_street,
                'billing_postcode': subject.billing_postcode,
                'billing_city': subject.billing_city,
                'billing_country': subject.billing_country,
                'reg_id': subject.reg_id,
                'tax_id': subject.tax_id,
                'vat_id': subject.vat_id,
                'email': subject.email,
                'phone': subject.phone,
            }

        not_empty_details = {k: v for k, v in details.items() if v not in EMPTY_VALUES}

        return not_empty_details

    def get_initial(self):
        initial = super().get_initial()
        user = self.object.user
        last_user_order = user.order_set.last()

        if last_user_order:
            # details from last order
            initial.update(self.get_cart_details(last_user_order))
        else:
            # details from order user / purchaser
            initial.update(self.get_cart_details(user))

        # details from cart itself (the highest priority)
        initial.update(self.get_cart_details(self.object))

        return initial

    def form_valid(self, form):
        form.save()
        return redirect('commerce:checkout_shipping_and_payment')


class CheckoutShippingAndPaymentView(CartMixin, EmptyCartRedirectMixin, UpdateView):
    template_name = 'commerce/checkout_form.html'
    form_class = ShippingAndPaymentForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        shipping_options = ShippingOption.objects.for_country(self.object.delivery_country)
        payment_methods = PaymentMethod.objects.all()

        if shipping_options.count() == 1 and payment_methods.count() == 1:
            if shipping_options.first().fee == 0 and payment_methods.first().fee == 0:
                form_kwargs = self.get_form_kwargs()
                form_kwargs.update({'data': self.get_initial()})
                form = self.get_form_class()(**form_kwargs)

                if form.is_valid():
                    return self.form_valid(form)
                else:
                    return self.form_invalid(form)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return redirect('commerce:checkout_summary')

    def get_initial(self):
        initial = super().get_initial()

        shipping_options = ShippingOption.objects.for_country(self.object.delivery_country)

        if shipping_options.count() == 1:
            initial.update({
                'shipping_option': shipping_options.first()
            })

        payment_methods = PaymentMethod.objects.all()

        if payment_methods.count() == 1:
            initial.update({
                'payment_method': payment_methods.first()
            })

        return initial


class CheckoutSummaryView(CartMixin, EmptyCartRedirectMixin, DetailView):
    template_name = 'commerce/checkout_summary.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            'loyalty_program_enabled': commerce_settings.LOYALTY_PROGRAM_ENABLED,
            'unit_price_is_with_tax': commerce_settings.UNIT_PRICE_IS_WITH_TAX,
        })
        return context_data


class CheckoutFinishView(CartMixin, DetailView):
    def get(self, request, *args, **kwargs):
        cart = self.get_object()

        # if cart can not be finished, redirect back to cart detail
        if not cart.can_be_finished():
            messages.warning(request, _('Checkout process can not be finished yet'))
            return redirect(cart.get_absolute_url())

        # set order status depending on cart total value
        order_status = Order.STATUS_AWAITING_PAYMENT if cart.total > 0 else Order.STATUS_PENDING
        order = cart.to_order(status=order_status)

        if order.status != Order.STATUS_AWAITING_PAYMENT:
            return redirect(self.get_checkout_finish_url(order))

        if not order.payment_method:
            messages.error(request, _('Missing payment method'))
            return redirect(self.get_checkout_finish_url(order))

        if order.payment_method.method == PaymentMethod.METHOD_ONLINE_PAYMENT:
            return redirect(order.get_payment_url())

        return redirect(self.get_checkout_finish_url(order))

    def get_checkout_finish_url(self, order):
        if commerce_settings.CHECKOUT_FINISH_URL:
            return commerce_settings.CHECKOUT_FINISH_URL
        return order.get_absolute_url()
