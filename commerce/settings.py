from django.conf import settings


CURRENCY = getattr(settings, 'COMMERCE_CURRENCY', 'EUR')
PAYMENT_MANAGER = getattr(settings, 'COMMERCE_PAYMENT_MANAGER', 'commerce.managers.PaymentManager')
IBAN = getattr(settings, 'COMMERCE_IBAN', '')
