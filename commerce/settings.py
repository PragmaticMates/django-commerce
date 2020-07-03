from django.conf import settings


CURRENCY = getattr(settings, 'COMMERCE_CURRENCY', 'EUR')
PAYMENT_MANAGER = getattr(settings, 'COMMERCE_PAYMENT_MANAGER', 'commerce.managers.PaymentManager')
IBAN = getattr(settings, 'COMMERCE_IBAN', '')
USE_RQ = getattr(settings, 'COMMERCE_USE_RQ', True)
REDIS_QUEUE = getattr(settings, 'COMMERCE_REDIS_QUEUE', 'default')
