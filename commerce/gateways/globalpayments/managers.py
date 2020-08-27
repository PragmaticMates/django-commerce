import base64
from OpenSSL import crypto
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from commerce.gateways.globalpayments.models import Result
from commerce.models import Order
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
        url = self.get_gateway_url()
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

    def handle_payment_result(self, data):
        # TODO: validation of signature

        result, created = Result.objects.get_or_create(
            order_id=data['ORDERNUMBER'],
            operation=data['OPERATION'],
            ordernumber=int(data['ORDERNUMBER']),
            meordernum=int(data['MEORDERNUM']) if 'MEORDERNUM' in data else None,
            md=data.get('MD', ''),
            prcode=int(data['PRCODE']),
            srcode=int(data['SRCODE']),
            resulttext=data.get('RESULTTEXT', ''),
            userparam1=data.get('USERPARAM1', ''),
            addinfo=data.get('ADDINFO', ''),
            token=data.get('TOKEN', ''),
            expiry=data.get('EXPIRY', ''),
            acsres=data.get('ACSRES', ''),
            accode=data.get('ACCODE', ''),
            panpattern=data.get('PANPATTERN', ''),
            daytocapture=data.get('DAYTOCAPTURE', ''),
            tokenregstatus=data.get('TOKENREGSTATUS', ''),
            acrc=data.get('ACRC', ''),
            rrn=data.get('RRN', ''),
            par=data.get('PAR', ''),
            traceid=data.get('TRACEID', ''),
            digest=data['DIGEST'],
            digest1=data['DIGEST1'],
        )

        if result.prcode == 50:
            # The cardholder canceled the payment
            return False, None

        # check primary result code
        if result.prcode != 0:
            return False, '{} {}'.format(_('Payment failed. Error detail:'), result.resulttext)

        # check if order order/transaction id is correct
        if not self.order.order_set.filter(id=result.ordernumber).exists():
            return False, _('Transaction not recognised')

        # PRCODE = 0 => OK
        if result.prcode == 0:
            from commerce.gateways.globalpayments.models import Order as GPOrder
            gporder = GPOrder.objects.get(pk=result.ordernumber)
            gporder.status = GPOrder.STATUS_PAID
            gporder.save(update_fields=['status'])

            if self.order.status == Order.STATUS_AWAITING_PAYMENT:
                # TODO: check order total
                self.order.status = Order.STATUS_PAYMENT_RECEIVED
                self.order.save(update_fields=['status'])
                return True, _('Order successfully paid.')
            # TODO: check different order statuses

        return False, _('Payment without result.')
