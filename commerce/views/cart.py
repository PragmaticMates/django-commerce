from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import DetailView

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

        back_url = request.GET.get('back_url', reverse('commerce:cart'))
        return redirect(back_url)


class CartDetailView(LoginRequiredMixin, DetailView):
    model = Cart

    def get_object(self, queryset=None):
        return self.model.get_for_user(self.request.user)
