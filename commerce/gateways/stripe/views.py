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
from commerce.models import Order, Discount
from inventor.templatetags.inventor import uri

stripe.api_key = commerce_settings.GATEWAY_STRIPE_SECRET_API_KEY


# If you are testing your webhook locally with the Stripe CLI you
# can find the endpoint's secret by running `stripe listen`
# Otherwise, find your endpoint's secret in your webhook settings in the Developer Dashboard
endpoint_secret = commerce_settings.GATEWAY_STRIPE_ENDPOINT_SECRET


# TODO: check useful functionality: https://medium.com/geekculture/how-to-integrate-stripe-in-django-1f7b8e83c0a8
# TODO: check useful functionality: https://justdjango.com/blog/django-stripe-payments-tutorial
# TODO: https://stripe.com/docs/payments/accept-a-payment?platform=web&ui=checkout
# TODO: https://testdriven.io/blog/django-stripe-tutorial/

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

        if order.loyalty_points_used > 0 or order.discount and order.discount.unit == Discount.UNIT_CURRENCY:
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

            if order.shipping_fee > 0:
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

            if order.payment_fee > 0:
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

            # stripe does not support negative items !!!
            # if order.loyalty_points_used > 0:
            #     line_items.append({
            #         'price_data': {
            #             'currency': commerce_settings.CURRENCY.lower(),
            #             'unit_amount': -int(points_to_currency_unit(order.loyalty_points_used) * 100),
            #             'product_data': {
            #                 'name': _('Credit'),
            #             },
            #         },
            #         'quantity': 1,
            #     })

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
            # TODO: check functionality
            # return redirect(checkout_session.url)
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

        try:
            sig_header = request.META['HTTP_STRIPE_SIGNATURE']
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            # Invalid payload
            return HttpResponse(status=400)
        except KeyError as e:
            # Missing signature
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return HttpResponse(status=400)

        # Handle the event
        if event.type == 'payment_intent.created':
            print('PaymentIntent was created!')

        elif event.type == 'payment_method.attached':
            print('PaymentMethod was attached to a Customer!')

        elif event.type == 'charge.succeeded':
            print('Charge was successful!')

            # customer doesn't have to be created yet!
            # charge = event.data.object  # contains a stripe.Charge
            # customer = Customer.objects.get(stripe_id=charge.customer)
            # customer.payment_method = charge.payment_method
            # customer.save(update_fields=['payment_method'])

        elif event.type == 'customer.created':
            print('Customer was created!')
            customer = event.data.object
            user = get_user_model().objects.get(email=customer.email)
            Customer.objects.update_or_create(user=user, defaults={'stripe_id': customer.id})

        elif event.type == 'payment_intent.succeeded':
            print('PaymentIntent was successful!')
            intent = event.data.object  # contains a stripe.PaymentIntent
            customer = Customer.objects.get(stripe_id=intent.customer)
            customer.payment_method = intent.payment_method
            customer.save(update_fields=['payment_method'])

        elif event.type == 'checkout.session.completed':
            print('Checkout Session was completed!')
            session = event.data.object

            if session.payment_status == 'paid':
                order_number = int(session.client_reference_id)
                order = Order.objects.get(number=order_number)
                order.status = Order.STATUS_PAYMENT_RECEIVED
                order.save(update_fields=['status'])
        else:
            print('Unhandled event type {}'.format(event.type))

        return HttpResponse(status=200)
