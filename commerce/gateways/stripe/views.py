import json
import stripe
from django.contrib import messages
from django.contrib.auth import get_user_model

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView

from commerce import settings as commerce_settings
from commerce.gateways.stripe.models import Customer
from commerce.loyalty import points_to_currency_unit
from commerce.models import Order
from inventor.templatetags.inventor import uri

stripe.api_key = commerce_settings.GATEWAY_STRIPE_SECRET_API_KEY


# If you are testing your webhook locally with the Stripe CLI you
# can find the endpoint's secret by running `stripe listen`
# Otherwise, find your endpoint's secret in your webhook settings in the Developer Dashboard
endpoint_secret = commerce_settings.GATEWAY_STRIPE_ENDPOINT_SECRET


class StripeCreateSessionView(DetailView):
    model = Order

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()

        if order.status != Order.STATUS_AWAITING_PAYMENT:
            return HttpResponse(content=json.dumps({'error': _('It is not possible to pay this order anymore.')}), status=403)

        try:
            customer = request.user.customer
        except:
            customer = None

        line_items = []

        if order.loyalty_points_used > 0:
            # Stripe does not support items with negative amount (credit)
            line_items.append({
                'price_data': {
                    'currency': commerce_settings.CURRENCY.lower(),
                    'unit_amount': order.total_in_cents,
                    'product_data': {
                        'name': '%s %s' % (_('Order number'), str(order)),
                    },
                },
                'quantity': 1,
            })
        else:
            for purchaseditem in order.purchaseditem_set.all():
                line_items.append({
                    'price_data': {
                        'currency': commerce_settings.CURRENCY.lower(),
                        'unit_amount': int(purchaseditem.price * 100),
                        'product_data': {
                            'name': purchaseditem.title_with_option,
                        },
                    },
                    'quantity': purchaseditem.quantity,
                })

            line_items.append({
                'price_data': {
                    'currency': commerce_settings.CURRENCY.lower(),
                    'unit_amount': int(order.shipping_fee * 100),
                    'product_data': {
                        'name': _('Shipping fee'),
                    },
                },
                'quantity': 1,
            })

            line_items.append({
                'price_data': {
                    'currency': commerce_settings.CURRENCY.lower(),
                    'unit_amount': int(order.payment_fee * 100),
                    'product_data': {
                        'name': _('Payment fee'),
                    },
                },
                'quantity': 1,
            })

            line_items.append({
                'price_data': {
                    'currency': commerce_settings.CURRENCY.lower(),
                    'unit_amount': -int(points_to_currency_unit(order.loyalty_points_used) * 100),
                    'product_data': {
                        'name': _('Credit'),
                    },
                },
                'quantity': 1,
            })

        try:
            # TODO: billing
            checkout_session = stripe.checkout.Session.create(
                customer=customer.stripe_id if customer else None,
                customer_email=request.user.email if not customer else None,
                client_reference_id=order.number,
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=uri({'request': request}, reverse('commerce:stripe_success_payment')),
                cancel_url=uri({'request': request}, reverse('commerce:stripe_cancel_payment')),
            )
            return HttpResponse(json.dumps({'id': checkout_session.id}), status=200)
        except Exception as e:
            print('ERROR', e)
            return HttpResponse(content=json.dumps({'error': str(e)}), status=403)


class StripeSuccessPaymentView(View):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, _('Payment was successful.'))
        # TODO
        return redirect(reverse('commerce:orders'))


class StripeCancelPaymentView(View):
    def dispatch(self, request, *args, **kwargs):
        messages.error(request, _('Payment failed.'))
        return redirect(reverse('commerce:orders'))


class StripeWebhookView(View):
    # https://stripe.com/docs/webhooks/signatures

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            # Invalid payload
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return HttpResponse(status=400)

        # Handle the event
        if event.type == 'customer.created':
            customer = event.data.object
            user = get_user_model().objects.get(email=customer.email)
            stripe_id = customer.id
            Customer.objects.get_or_create(user=user, stripe_id=stripe_id)
        elif event.type == 'payment_intent.succeeded':
            payment_intent = event.data.object  # contains a stripe.PaymentIntent
            print('payment_intent')
            print(payment_intent)
            print('PaymentIntent was successful!')
        elif event.type == 'payment_method.attached':
            payment_method = event.data.object  # contains a stripe.PaymentMethod
            print('payment_method')
            print(payment_method)
            print('PaymentMethod was attached to a Customer!')
        # ... handle other event types
        elif event.type == 'charge.succeeded':
            charge = event.data.object  # contains a stripe.PaymentIntent
            print('charge')
            print(charge)
            # {
            #   "amount": 1234,
            #   "amount_captured": 1234,
            #   "amount_refunded": 0,
            #   "application": null,
            #   "application_fee": null,
            #   "application_fee_amount": null,
            #   "balance_transaction": "txn_0HcaIdrkd6LGXRyRAfzadtYz",
            #   "billing_details": {
            #     "address": {
            #       "city": null,
            #       "country": "SK",
            #       "line1": null,
            #       "line2": null,
            #       "postal_code": null,
            #       "state": null
            #     },
            #     "email": "erik.telepovsky@gmail.com",
            #     "name": "Erik TEST",
            #     "phone": null
            #   },
            #   "calculated_statement_descriptor": "PRAGMATIC MATES S.R.O.",
            #   "captured": true,
            #   "created": 1602783095,
            #   "currency": "eur",
            #   "customer": "cus_ID0JIfOv7N4nrC",
            #   "description": null,
            #   "destination": null,
            #   "dispute": null,
            #   "disputed": false,
            #   "failure_code": null,
            #   "failure_message": null,
            #   "fraud_details": {},
            #   "id": "ch_0HcaIdrkd6LGXRyRzeL8mH39",
            #   "invoice": null,
            #   "livemode": false,
            #   "metadata": {},
            #   "object": "charge",
            #   "on_behalf_of": null,
            #   "order": null,
            #   "outcome": {
            #     "network_status": "approved_by_network",
            #     "reason": null,
            #     "risk_level": "normal",
            #     "risk_score": 0,
            #     "seller_message": "Payment complete.",
            #     "type": "authorized"
            #   },
            #   "paid": true,
            #   "payment_intent": "pi_0HcaHlrkd6LGXRyRy79xrrXb",
            #   "payment_method": "pm_0HcaIcrkd6LGXRyRAkg7pppP",
            #   "payment_method_details": {
            #     "card": {
            #       "brand": "visa",
            #       "checks": {
            #         "address_line1_check": null,
            #         "address_postal_code_check": null,
            #         "cvc_check": "pass"
            #       },
            #       "country": "US",
            #       "exp_month": 12,
            #       "exp_year": 2021,
            #       "fingerprint": "f5Ecosg12vyKOSgO",
            #       "funding": "credit",
            #       "installments": null,
            #       "last4": "4242",
            #       "network": "visa",
            #       "three_d_secure": null,
            #       "wallet": null
            #     },
            #     "type": "card"
            #   },
            #   "receipt_email": null,
            #   "receipt_number": null,
            #   "receipt_url": "https://pay.stripe.com/receipts/acct_0cnprkd6LGXRyR9vKKmQ/ch_0HcaIdrkd6LGXRyRzeL8mH39/rcpt_ID0Jnz9PEQ3kBrXlGNGteqIfZXwPtNK",
            #   "refunded": false,
            #   "refunds": {
            #     "data": [],
            #     "has_more": false,
            #     "object": "list",
            #     "total_count": 0,
            #     "url": "/v1/charges/ch_0HcaIdrkd6LGXRyRzeL8mH39/refunds"
            #   },
            #   "review": null,
            #   "shipping": null,
            #   "source": null,
            #   "source_transfer": null,
            #   "statement_descriptor": null,
            #   "statement_descriptor_suffix": null,
            #   "status": "succeeded",
            #   "transfer_data": null,
            #   "transfer_group": null
            # }
        elif event.type == 'checkout.session.completed':
            session = event.data.object

            if session.payment_status == 'paid':
                order_number = int(session.client_reference_id)
                order = Order.objects.get(number=order_number)
                order.status = Order.STATUS_PAYMENT_RECEIVED
                order.save(update_fields=['status'])
        else:
            print('Unhandled event type {}'.format(event.type))
            # payment_intent.created
            # checkout.session.completed

        return HttpResponse(status=200)
