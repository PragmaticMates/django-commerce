import base64
from OpenSSL import crypto
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from inventor.templatetags.inventor import uri
from commerce import settings as commerce_settings
from commerce.managers import PaymentManager as CommercePaymentManager


class PaymentManager(CommercePaymentManager):
    def render_payment_button(self):
        label = _('Pay')
        url = self.order.get_payment_url()
        return mark_safe(f'<a href="{uri({}, url)}" class="btn btn-primary">{label}</a>')

    def render_payment_information(self):
        return ''

    def get_payment_url(self):
        from commerce.gateways.globalpayments.models import Order as GPOrder
        GPOrder.objects.create(order=self.order)

        payment_data = {
            'order': self.order,
            'MERCHANTNUMBER': commerce_settings.GATEWAY_GP_MERCHANT_NUMBER,
            'OPERATION': 'CREATE_ORDER',
            'ORDERNUMBER': self.order.order_set.latest().id,
            'AMOUNT': self.order.total_in_cents,
            'CURRENCY': '',  # empty value is default value of payment gateway merchant eshop
            'DEPOSITFLAG': 1,
            'MERORDERNUM': self.order.number,
            'URL': uri({}, self.order.get_payment_return_url()),  # absolute URL
            'REFERENCENUMBER': self.order.id
        }

        digest = self.get_digest(payment_data)
        payment_data.update({'DIGEST': digest})

        params = urlencode(payment_data)
        url = commerce_settings.GATEWAY_GP_URL_TEST
        payment_url = f'{url}?{params}'
        return payment_url

    def get_gateway_url(self):
        debug = commerce_settings.GATEWAY_GP_DEBUG
        return commerce_settings.GATEWAY_GP_URL_TEST if debug else commerce_settings.GATEWAY_GP_URL

    def get_digest(self, payment_data):
        d = payment_data

        # MERCHANTNUMBER + | + OPERATION + | + ORDERNUMBER + | + AMOUNT + | + CURRENCY + | + DEPOSITFLAG + | + MERORDERNUM + | + URL + | + REFERENCENUMBER
        digest_input = f'{d["MERCHANTNUMBER"]}|{d["OPERATION"]}|{d["ORDERNUMBER"]}|{d["AMOUNT"]}|{d["CURRENCY"]}|{d["DEPOSITFLAG"]}|{d["MERORDERNUM"]}|{d["URL"]}|{d["REFERENCENUMBER"]}'

        private_key = {
            'path': commerce_settings.GATEWAY_GP_PRIVATE_KEY_PATH,
            'password': commerce_settings.GATEWAY_GP_PRIVATE_KEY_PASSWORD
        }

        with open(private_key['path'], "r") as key_file:
            key = key_file.read()

        password = private_key['password'].encode('ascii')

        pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, key, password)
        sign = crypto.sign(pkey, digest_input, "sha1")
        data_base64 = base64.b64encode(sign)
        digest = data_base64.decode("utf-8")
        return digest
