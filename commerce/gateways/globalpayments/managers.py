import base64

import unidecode
from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from OpenSSL import crypto
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from commerce import settings as commerce_settings
from commerce.gateways.globalpayments.models import Payment, Result
from commerce.managers import PaymentManager as CommercePaymentManager
from commerce.models import Order

from inventor.templatetags.inventor import uri  # TODO: move to pragmatic


class PaymentManager(CommercePaymentManager):
    def render_payment_button(self):
        label = _('Pay')
        url = self.order.get_payment_url()
        return mark_safe(f'<a href="{uri({}, url)}" class="btn btn-primary">{label}</a>')

    def render_payment_information(self):
        return ''

    def get_payment_url(self):
        # get payment data from order details
        payment_data = self.payment_data

        # generate and sign digest
        digest = self.get_digest(payment_data)
        payment_data.update({'DIGEST': digest})

        # URL encode
        params = urlencode(payment_data)
        url = self.get_gateway_url()
        payment_url = f'{url}?{params}'
        return payment_url

    def get_gateway_url(self):
        debug = commerce_settings.GATEWAY_GP_DEBUG
        return commerce_settings.GATEWAY_GP_URL_TEST if debug else commerce_settings.GATEWAY_GP_URL

    @property
    def payment_data(self):
        payment = Payment.objects.create(order=self.order)

        description = ', '.join([str(item) for item in self.order.purchaseditem_set.all()])
        description = unidecode.unidecode(description)

        return {
            'order': self.order,
            'MERCHANTNUMBER': commerce_settings.GATEWAY_GP_MERCHANT_NUMBER,
            'OPERATION': 'CREATE_ORDER',
            'ORDERNUMBER': self.get_order_number_from_payment_id(payment.id),
            'AMOUNT': self.order.total_in_cents,
            'CURRENCY': '',  # empty value is default value of payment gateway merchant eshop
            'DEPOSITFLAG': 1,
            'MERORDERNUM': self.order.number,
            'URL': uri({}, self.order.get_payment_return_url()),  # absolute URL
            'DESCRIPTION': description[:255],
            'REFERENCENUMBER': self.order.id
        }

    def get_digest(self, payment_data=None):
        d = payment_data or self.payment_data

        # MERCHANTNUMBER + | + OPERATION + | + ORDERNUMBER + | + AMOUNT + | + CURRENCY + | + DEPOSITFLAG + | + MERORDERNUM + | + URL + | + REFERENCENUMBER
        digest_input = f'{d["MERCHANTNUMBER"]}|{d["OPERATION"]}|{d["ORDERNUMBER"]}|{d["AMOUNT"]}|{d["CURRENCY"]}|{d["DEPOSITFLAG"]}|{d["MERORDERNUM"]}|{d["URL"]}|{d["DESCRIPTION"]}|{d["REFERENCENUMBER"]}'

        # sign
        digest = self.sign(digest_input)
        return digest

    def sign(self, data):
        private_key = {
            'path': commerce_settings.GATEWAY_GP_PRIVATE_KEY_PATH,
            'password': commerce_settings.GATEWAY_GP_PRIVATE_KEY_PASSWORD
        }

        with open(private_key['path'], "r") as key_file:
            key = key_file.read()

        password = private_key['password'].encode('ascii')

        pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, key, password)
        signed_data = crypto.sign(pkey, data, "sha1")
        signed_data_encoded = base64.b64encode(signed_data)
        return signed_data_encoded.decode("utf-8")

    def verify(self, signature, data):
        '''
        Verifies with a public key from whom the data came that it was indeed
        signed by their private key
        param: public_key_loc Path to public key
        param: signature String signature to be verified
        return: Boolean. True if the signature is valid; False otherwise.
        '''
        pub_key = open(commerce_settings.GATEWAY_GP_PUBLIC_KEY_PATH, "r").read()
        rsakey = RSA.importKey(pub_key)
        signer = PKCS1_v1_5.new(rsakey)
        digest = SHA1.new()
        digest.update(data.encode("utf-8"))
        return signer.verify(digest, base64.b64decode(signature))

    def get_payment_id_from_order_number(self, order_number):
        return order_number - commerce_settings.GATEWAY_GP_ORDER_NUMBER_STARTS_FROM + 1

    def get_order_number_from_payment_id(self, payment_id):
        return payment_id + commerce_settings.GATEWAY_GP_ORDER_NUMBER_STARTS_FROM - 1

    def handle_payment_result(self, data):
        payment_id = self.get_payment_id_from_order_number(int(data['ORDERNUMBER']))

        result, created = Result.objects.get_or_create(
            payment_id=payment_id,
            operation=data['OPERATION'],
            ordernumber=int(data['ORDERNUMBER']),
            merordernum=int(data['MERORDERNUM']) if 'MERORDERNUM' in data else None,
            md=data.get('MD', None),
            prcode=int(data['PRCODE']),
            srcode=int(data['SRCODE']),
            resulttext=data.get('RESULTTEXT', None),
            userparam1=data.get('USERPARAM1', None),
            addinfo=data.get('ADDINFO', None),
            token=data.get('TOKEN', None),
            expiry=data.get('EXPIRY', None),
            acsres=data.get('ACSRES', None),
            accode=data.get('ACCODE', None),
            panpattern=data.get('PANPATTERN', None),
            daytocapture=data.get('DAYTOCAPTURE', None),
            tokenregstatus=data.get('TOKENREGSTATUS', None),
            acrc=data.get('ACRC', None),
            rrn=data.get('RRN', None),
            par=data.get('PAR', None),
            traceid=data.get('TRACEID', None),
            digest=data['DIGEST'],
            digest1=data['DIGEST1'],
        )

        # Check payment signature
        if not result.is_valid():
            return False, '{} {}'.format(_('Invalid payment signature.'), result.resulttext)

        # The cardholder canceled the payment
        if result.prcode == 50:
            return False, None

        # check primary result code
        if result.prcode != 0:
            return False, '{} {}'.format(_('Payment failed. Error detail:'), result.resulttext)

        # check if order order/transaction id is correct
        if not self.order.payment_set.filter(id=payment_id).exists():
            return False, _('Transaction not recognised')

        # PRCODE = 0 => OK
        if result.prcode == 0:
            payment = Payment.objects.get(pk=payment_id)
            payment.status = Payment.STATUS_PAID
            payment.save(update_fields=['status'])

            if self.order.status == Order.STATUS_AWAITING_PAYMENT:
                # TODO: check order total
                self.order.status = Order.STATUS_PAYMENT_RECEIVED
                self.order.save(update_fields=['status'])
                return True, _('Order successfully paid.')
            # TODO: check different order statuses

        return False, _('Payment without result.')
