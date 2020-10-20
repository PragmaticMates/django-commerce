from django.template.loader import get_template
from django.urls import reverse

from commerce import settings as commerce_settings
from commerce.managers import PaymentManager as CommercePaymentManager


class PaymentManager(CommercePaymentManager):
    def get_payment_url(self):
        return reverse('commerce:orders')

    def render_payment_button(self):
        template = get_template('commerce/payment_button_wire_transfer.html')
        return template.render({'order': self.order})

    def render_payment_information(self):
        template = get_template('commerce/payment_information_wire_transfer.html')
        return template.render({'order': self.order, 'commerce_settings': commerce_settings})
