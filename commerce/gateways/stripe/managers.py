from django.template import loader
from django.urls import reverse

from commerce import settings as commerce_settings
from commerce.managers import PaymentManager as CommercePaymentManager


class PaymentManager(CommercePaymentManager):
    def render_payment_button(self):
        template = loader.get_template('commerce/stripe_button.html')
        return template.render({
            'order': self.order,
            'stripe_key': commerce_settings.GATEWAY_STRIPE_PUBLISHABLE_API_KEY,
        })

    def render_payment_information(self):
        return ''

    def get_payment_url(self):
        url = reverse('commerce:orders')
        return f'{url}?pay={self.order.id}'

    # def get_order_number_from_payment_id(self, session):
    #     # TODO
    #     pass

    def handle_payment_result(self, data):
        # TODO
        pass
