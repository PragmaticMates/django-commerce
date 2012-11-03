from form_utils.forms import BetterModelForm

from django import forms
from django.utils.translation import ugettext_lazy as _

from commerce.utils.cart import get_cart
from commerce.models.order import Order
from commerce.app_settings import COMMERCE_SHIPPINGS, COMMERCE_PAYMENTS, \
    COMMERCE_SHIPPINGS_PAYMENTS, COMMERCE_PAYMENTS


class ShippingPaymentForm(BetterModelForm):
    shipping = forms.CharField(
        label=_(u'Shipping'),
        widget=forms.RadioSelect(choices=COMMERCE_SHIPPINGS))
    payment = forms.CharField(
        label=_(u'Payment'),
        widget=forms.RadioSelect(choices=COMMERCE_PAYMENTS))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ShippingPaymentForm, self).__init__(*args, **kwargs)

    def formatted_shipping(self):
        shipping = self.initial.get('shipping', None)
        for method in COMMERCE_SHIPPINGS:
            if method[0] == shipping:
                return method[1]
        return None

    def formatted_payment(self):
        payment = self.initial.get('payment', None)
        for method in COMMERCE_PAYMENTS:
            if method[0] == payment:
                return method[1]
        return None

    def price(self):
        initial = self.initial.get('shipping', None)
        for shipping in COMMERCE_SHIPPINGS_PAYMENTS:
            if shipping[0] == initial:
                if type(shipping[1]) is tuple:
                    cart = get_cart(self.request)
                    price_cart = cart.total()
                    price_current = None

                    for sub_shipping in shipping[1]:
                        if price_current is None:
                            price_current = sub_shipping[2]
                        elif sub_shipping[0] < price_cart <= sub_shipping[1]:
                            price_current = sub_shipping[2]
                    return price_current
                return shipping[1]
        return 0

    class Meta:
        model = Order
        fieldsets = [
            (_(u'Shipping'), {
                'fields': ('shipping', ),
                'classes': ('shipping', ),
            }),
            (_(u'Payment'), {
                'fields': ('payment', ),
                'classes': ('payment', ),
            })
        ]
        widgets = {
            'shipping': forms.RadioSelect(),
            'payment': forms.RadioSelect(),
        }
