from django.conf import settings


CURRENCY = getattr(settings, 'COMMERCE_CURRENCY', 'EUR')
PAYMENT_MANAGER = getattr(settings, 'COMMERCE_PAYMENT_MANAGER', 'commerce.managers.PaymentManager')
IBAN = getattr(settings, 'COMMERCE_IBAN', '')
BIC_SWIFT = getattr(settings, 'COMMERCE_BIC_SWIFT', '')
BANK_NAME = getattr(settings, 'COMMERCE_BANK_NAME', '')
BANK_ADDRESS = getattr(settings, 'COMMERCE_BANK_ADDRESS', '')
RECIPIENT = getattr(settings, 'COMMERCE_RECIPIENT', '')
RECIPIENT_ADDRESS = getattr(settings, 'COMMERCE_RECIPIENT_ADDRESS', '')
USE_RQ = getattr(settings, 'COMMERCE_USE_RQ', True)
REDIS_QUEUE = getattr(settings, 'COMMERCE_REDIS_QUEUE', 'default')
ORDER_NUMBER_STARTS_FROM = getattr(settings, 'COMMERCE_ORDER_NUMBER_STARTS_FROM', 1)
BANK_API_TOKEN = getattr(settings, 'COMMERCE_BANK_API_TOKEN', None)
BANK_API = getattr(settings, 'COMMERCE_BANK_API', None)
